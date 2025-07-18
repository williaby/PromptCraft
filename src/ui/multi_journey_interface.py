"""
Multi-Journey Gradio Interface for PromptCraft-Hybrid

This module provides the unified interface supporting all four user journeys:
- Journey 1: Smart Templates (C.R.E.A.T.E. framework)
- Journey 2: Intelligent Search (HyDE-powered)
- Journey 3: IDE Integration (Code-Server launcher)
- Journey 4: Autonomous Workflows (with Free Mode toggle)

Implements comprehensive file upload, OpenRouter model selection,
and code snippet copying functionality.
"""

import logging
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import gradio as gr

from src.config.settings import ApplicationSettings
from src.utils.logging_mixin import LoggerMixin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter to prevent DoS attacks through request flooding.

    Implements sliding window rate limiting with separate limits for:
    - General requests per minute/hour
    - File uploads per hour
    """

    def __init__(
        self,
        max_requests_per_minute: int = 30,
        max_requests_per_hour: int = 200,
        max_file_uploads_per_hour: int = 50,
    ):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_hour = max_requests_per_hour
        self.max_file_uploads_per_hour = max_file_uploads_per_hour

        # Track requests per session using sliding windows
        self.request_windows: dict[str, deque] = defaultdict(deque)
        self.file_upload_windows: dict[str, deque] = defaultdict(deque)

        # Cleanup old entries periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def _cleanup_old_entries(self) -> None:
        """Remove old entries to prevent memory leaks."""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = current_time - 3600  # Remove entries older than 1 hour

        # Clean request windows
        for session_id in list(self.request_windows.keys()):
            window = self.request_windows[session_id]
            while window and window[0] < cutoff_time:
                window.popleft()
            if not window:
                del self.request_windows[session_id]

        # Clean file upload windows
        for session_id in list(self.file_upload_windows.keys()):
            window = self.file_upload_windows[session_id]
            while window and window[0] < cutoff_time:
                window.popleft()
            if not window:
                del self.file_upload_windows[session_id]

        self.last_cleanup = current_time

    def check_request_rate(self, session_id: str) -> bool:
        """
        Check if request is within rate limits and record the request.

        Args:
            session_id: Unique session identifier

        Returns:
            True if request is allowed, False if rate limited
        """
        self._cleanup_old_entries()

        current_time = time.time()
        window = self.request_windows[session_id]

        # Remove requests older than 1 hour
        while window and window[0] < current_time - 3600:
            window.popleft()

        # Count requests in last minute and hour
        minute_cutoff = current_time - 60
        requests_last_minute = sum(1 for timestamp in window if timestamp > minute_cutoff)
        requests_last_hour = len(window)

        # Check limits
        if requests_last_minute >= self.max_requests_per_minute:
            return False
        if requests_last_hour >= self.max_requests_per_hour:
            return False

        # Record this request
        window.append(current_time)
        return True

    def check_file_upload_rate(self, session_id: str) -> bool:
        """
        Check if file upload is within rate limits and record the upload.

        Args:
            session_id: Unique session identifier

        Returns:
            True if upload is allowed, False if rate limited
        """
        self._cleanup_old_entries()

        current_time = time.time()
        window = self.file_upload_windows[session_id]

        # Remove uploads older than 1 hour
        while window and window[0] < current_time - 3600:
            window.popleft()

        # Check hourly limit
        if len(window) >= self.max_file_uploads_per_hour:
            return False

        # Record this upload
        window.append(current_time)
        return True

    def get_rate_limit_status(self, session_id: str) -> dict[str, Any]:
        """Get current rate limit status for a session."""
        current_time = time.time()

        # Request window
        request_window = self.request_windows.get(session_id, deque())
        minute_cutoff = current_time - 60
        requests_last_minute = sum(1 for timestamp in request_window if timestamp > minute_cutoff)
        requests_last_hour = len(request_window)

        # File upload window
        upload_window = self.file_upload_windows.get(session_id, deque())
        uploads_last_hour = len(upload_window)

        return {
            "requests_last_minute": requests_last_minute,
            "requests_last_hour": requests_last_hour,
            "uploads_last_hour": uploads_last_hour,
            "limits": {
                "max_requests_per_minute": self.max_requests_per_minute,
                "max_requests_per_hour": self.max_requests_per_hour,
                "max_file_uploads_per_hour": self.max_file_uploads_per_hour,
            },
        }


class MultiJourneyInterface(LoggerMixin):
    """
    Main Gradio interface supporting all four PromptCraft journeys.

    Features:
    - Tabbed interface for journey navigation
    - File upload with drag & drop support
    - OpenRouter model selection and cost tracking
    - Code snippet copying with multiple formats
    - Session management and data persistence
    """

    def __init__(self):
        super().__init__()
        self.settings = ApplicationSettings()
        # Remove shared instance variables that cause session corruption
        # self.session_state = {}  # REMOVED: Shared between users
        # self.current_journey = "journey_1"  # REMOVED: Shared between users
        # self.session_cost = 0.0  # REMOVED: Shared between users
        self.model_costs = self._load_model_costs()

        # Rate limiting configuration
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=30,  # 30 requests per minute per session
            max_requests_per_hour=200,  # 200 requests per hour per session
            max_file_uploads_per_hour=50,  # 50 file uploads per hour per session
        )

    def _load_model_costs(self) -> dict[str, float]:
        """Load model pricing information for cost tracking."""
        return {
            # Free models
            "llama-4-maverick:free": 0.0,
            "mistral-small-3.1:free": 0.0,
            "deepseek-chat:free": 0.0,
            "optimus-alpha:free": 0.0,
            # Standard models (cost per 1K tokens)
            "gpt-4o-mini": 0.0015,
            "gpt-3.5-turbo": 0.0005,
            "claude-3-haiku": 0.00025,
            "gemini-1.5-flash": 0.00035,
            # Premium models
            "gpt-4o": 0.015,
            "claude-3.5-sonnet": 0.003,
            "gemini-1.5-pro": 0.00125,
            "o1-preview": 0.015,
        }

    def _create_header(self) -> gr.HTML:
        """Create the header section with branding and model selection."""
        return gr.HTML(
            """
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #e2e8f0;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 24px;">🚀</span>
                <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #1e40af;">PromptCraft-Hybrid</h1>
                <span style="font-size: 14px; color: #64748b; margin-left: 10px;">Transform Ideas into Intelligence</span>
            </div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <div id="model-selector" style="background: #f1f5f9; padding: 6px 12px; border-radius: 6px; font-size: 14px; border: 1px solid #cbd5e1;">
                    Model: <span id="current-model">gpt-4o-mini</span>
                </div>
                <div id="cost-display" style="background: #10b981; color: white; padding: 6px 12px; border-radius: 6px; font-size: 14px; font-weight: 500;">
                    💰 Cost: $<span id="session-cost">0.00</span> | Mode: <span id="current-mode">Standard</span>
                </div>
            </div>
        </div>
        """,
        )

    def _create_model_selector(self) -> gr.Dropdown:
        """Create the model selection dropdown."""
        return gr.Dropdown(
            label="🤖 AI Model Selection",
            choices=[
                ("🆓 Free Only Mode", "free_mode"),
                ("⚡ Standard Routing", "standard"),
                ("🚀 Premium Routing", "premium"),
                ("🎯 Custom Model Selection", "custom"),
            ],
            value="standard",
            elem_id="model-selector-dropdown",
        )

    def _create_custom_model_selector(self) -> gr.Dropdown:
        """Create the custom model selection dropdown."""
        return gr.Dropdown(
            label="Select Specific Model",
            choices=[
                # Free models
                ("🆓 Llama 4 Maverick (Free)", "llama-4-maverick:free"),
                ("🆓 Mistral Small 3.1 (Free)", "mistral-small-3.1:free"),
                ("🆓 DeepSeek Chat (Free)", "deepseek-chat:free"),
                ("🆓 Optimus Alpha (Free)", "optimus-alpha:free"),
                # Standard models
                ("⚡ GPT-4o Mini ($0.0015/1K)", "gpt-4o-mini"),
                ("⚡ GPT-3.5 Turbo ($0.0005/1K)", "gpt-3.5-turbo"),
                ("⚡ Claude 3 Haiku ($0.00025/1K)", "claude-3-haiku"),
                ("⚡ Gemini 1.5 Flash ($0.00035/1K)", "gemini-1.5-flash"),
                # Premium models
                ("🚀 GPT-4o ($0.015/1K)", "gpt-4o"),
                ("🚀 Claude 3.5 Sonnet ($0.003/1K)", "claude-3.5-sonnet"),
                ("🚀 Gemini 1.5 Pro ($0.00125/1K)", "gemini-1.5-pro"),
                ("🚀 O1 Preview ($0.015/1K)", "o1-preview"),
            ],
            value="gpt-4o-mini",
            visible=False,
        )

    def _create_cost_tracker(self) -> gr.HTML:
        """Create the cost tracking display."""
        return gr.HTML(
            """
        <div style="background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0;">
            <h3 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600;">📊 Session Analytics</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px;">
                <div style="text-align: center; padding: 8px; background: white; border-radius: 4px;">
                    <div style="font-size: 18px; font-weight: 600; color: #1e293b;">$<span id="total-cost">0.00</span></div>
                    <div style="font-size: 12px; color: #64748b;">Total Cost</div>
                </div>
                <div style="text-align: center; padding: 8px; background: white; border-radius: 4px;">
                    <div style="font-size: 18px; font-weight: 600; color: #1e293b;"><span id="request-count">0</span></div>
                    <div style="font-size: 12px; color: #64748b;">Requests</div>
                </div>
                <div style="text-align: center; padding: 8px; background: white; border-radius: 4px;">
                    <div style="font-size: 18px; font-weight: 600; color: #1e293b;"><span id="avg-response-time">0.0</span>s</div>
                    <div style="font-size: 12px; color: #64748b;">Avg Response</div>
                </div>
                <div style="text-align: center; padding: 8px; background: white; border-radius: 4px;">
                    <div style="font-size: 18px; font-weight: 600; color: #1e293b;"><span id="free-requests">0</span>/1000</div>
                    <div style="font-size: 12px; color: #64748b;">Free Requests</div>
                </div>
            </div>
        </div>
        """,
        )

    def create_interface(self) -> gr.Blocks:
        """Create the main Gradio interface with all journeys."""

        # Custom CSS for styling
        custom_css = """
        .gradio-container {
            max-width: 1400px !important;
            margin: 0 auto !important;
        }

        .journey-header {
            text-align: center;
            margin-bottom: 24px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            color: white;
        }

        .journey-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .journey-subtitle {
            font-size: 16px;
            opacity: 0.9;
        }

        .input-section {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            background: white;
        }

        .model-attribution {
            background: #f8fafc;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 16px;
            border-left: 4px solid #3b82f6;
        }

        .code-block {
            background: #1e293b;
            color: #e2e8f0;
            padding: 16px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            position: relative;
            margin: 12px 0;
        }

        .file-upload-zone {
            border: 2px dashed #cbd5e1;
            border-radius: 8px;
            padding: 24px;
            text-align: center;
            background: #f8fafc;
            margin: 16px 0;
        }

        .file-upload-zone:hover {
            border-color: #3b82f6;
            background: #eff6ff;
        }

        .btn-primary {
            background: #3b82f6 !important;
            border: 1px solid #3b82f6 !important;
            color: white !important;
        }

        .btn-primary:hover {
            background: #2563eb !important;
            border-color: #2563eb !important;
        }

        .btn-secondary {
            background: #f8fafc !important;
            border: 1px solid #d1d5db !important;
            color: #374151 !important;
        }

        .btn-secondary:hover {
            background: #f1f5f9 !important;
        }

        .progress-indicator {
            background: #f1f5f9;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            margin-bottom: 16px;
        }
        """

        with gr.Blocks(css=custom_css, title="PromptCraft-Hybrid", theme=gr.themes.Soft()) as interface:

            # Session State Management (USER ISOLATION)
            session_state = gr.State(
                value={
                    "total_cost": 0.0,
                    "request_count": 0,
                    "current_journey": "journey_1",
                    "session_start_time": None,
                    "user_preferences": {},
                },
            )

            # Header
            header = self._create_header()

            # Model Selection Panel
            with gr.Row():
                with gr.Column(scale=3):
                    model_selector = self._create_model_selector()
                with gr.Column(scale=2):
                    custom_model_selector = self._create_custom_model_selector()
                with gr.Column(scale=2):
                    cost_tracker = self._create_cost_tracker()

            # Journey Navigation Tabs
            with gr.Tab("📝 Journey 1: Smart Templates") as journey1_tab:
                self._create_journey1_interface()

            with gr.Tab("🔍 Journey 2: Intelligent Search") as journey2_tab:
                self._create_journey2_interface()

            with gr.Tab("💻 Journey 3: IDE Integration") as journey3_tab:
                self._create_journey3_interface()

            with gr.Tab("🤖 Journey 4: Autonomous Workflows") as journey4_tab:
                self._create_journey4_interface()

            # Footer
            footer = gr.HTML(
                """
            <div style="margin-top: 32px; padding: 16px; border-top: 1px solid #e2e8f0; text-align: center; color: #64748b; font-size: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>Session: <span id="session-duration">0.0h</span> | Model: <span id="current-session-model">gpt-4o-mini</span> | Requests: <span id="session-requests">0</span></div>
                    <div>Status: 🟢 All systems operational | 🔄 Model Switch Available</div>
                    <div>Support: <a href="mailto:help@promptcraft.ai">help@promptcraft.ai</a></div>
                </div>
            </div>
            """,
            )

            # Event handlers
            model_selector.change(
                fn=self._on_model_selector_change,
                inputs=[model_selector],
                outputs=[custom_model_selector],
            )

        return interface

    def _create_journey1_interface(self):
        """Create Journey 1: Smart Templates interface with enhanced file upload."""
        # Initialize Journey 1 processor
        from src.ui.components.shared.export_utils import ExportUtils
        from src.ui.journeys.journey1_smart_templates import Journey1SmartTemplates

        journey1_processor = Journey1SmartTemplates()
        export_utils = ExportUtils()

        with gr.Column():
            # Journey Header
            gr.HTML(
                """
            <div class="journey-header">
                <div class="journey-title">Journey 1: Smart Templates</div>
                <div class="journey-subtitle">Transform rough ideas into polished prompts using the C.R.E.A.T.E. framework</div>
            </div>
            """,
            )

            # Input Section
            with gr.Group():
                gr.Markdown("### 📝 What would you like to enhance?")

                # Input method selector
                input_method = gr.Radio(
                    choices=["✏️ Text Input", "📁 File Upload", "🔗 URL Input", "📋 Clipboard"],
                    value="✏️ Text Input",
                    label="Input Method",
                )

                # Text input area
                text_input = gr.Textbox(
                    label="Describe your task or paste content",
                    placeholder="Describe your task, paste content, or upload files...",
                    lines=5,
                    max_lines=10,
                )

                # File upload section
                file_upload = gr.File(
                    label="📁 Upload Files (Supported: .txt, .md, .pdf, .docx, .csv, .json | Max: 10MB per file, 5 files max)",
                    file_count="multiple",
                    file_types=[".txt", ".md", ".pdf", ".docx", ".csv", ".json"],
                )

                # Configuration options
                with gr.Row():
                    reasoning_depth = gr.Dropdown(
                        choices=["basic", "detailed", "comprehensive"],
                        value="detailed",
                        label="🧠 Reasoning Depth",
                    )
                    search_tier = gr.Dropdown(
                        choices=["tier1", "tier2", "tier3"],
                        value="tier2",
                        label="🔄 Search Strategy",
                    )
                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=0.7,
                        step=0.1,
                        label="🌡️ Temperature",
                    )

                # Action buttons
                with gr.Row():
                    enhance_btn = gr.Button("🚀 Enhance Prompt", variant="primary", scale=2)
                    clear_btn = gr.Button("🗑️ Clear All", scale=1)
                    example_btn = gr.Button("📋 Load Example", scale=1)
                    save_btn = gr.Button("💾 Save Template", scale=1)

            # Output Section
            with gr.Group():
                gr.Markdown("### ✨ Enhanced Prompt Output")

                # Model attribution
                model_attribution = gr.HTML(
                    """
                <div class="model-attribution">
                    <strong>🤖 Generated by:</strong> <span id="j1-model-used">-</span> |
                    <strong>⏱️ Response time:</strong> <span id="j1-response-time">-</span> |
                    <strong>💰 Cost:</strong> $<span id="j1-cost">0.00</span>
                </div>
                """,
                )

                # Enhanced prompt display
                enhanced_prompt = gr.Textbox(
                    label="Enhanced Prompt",
                    lines=8,
                    max_lines=15,
                    interactive=False,
                )

                # C.R.E.A.T.E. breakdown accordion
                with gr.Accordion("📋 C.R.E.A.T.E. Framework Breakdown", open=False):
                    context_analysis = gr.Textbox(
                        label="C - Context Analysis",
                        lines=3,
                        interactive=False,
                    )
                    request_specification = gr.Textbox(
                        label="R - Request Specification",
                        lines=3,
                        interactive=False,
                    )
                    examples_section = gr.Textbox(
                        label="E - Examples & Demonstrations",
                        lines=3,
                        interactive=False,
                    )
                    augmentations_section = gr.Textbox(
                        label="A - Augmentations & Frameworks",
                        lines=3,
                        interactive=False,
                    )
                    tone_format = gr.Textbox(
                        label="T - Tone & Format Guidelines",
                        lines=3,
                        interactive=False,
                    )
                    evaluation_criteria = gr.Textbox(
                        label="E - Evaluation Criteria",
                        lines=3,
                        interactive=False,
                    )

                # File source attribution
                file_sources = gr.HTML(
                    """
                <div id="file-sources" style="background: #f8fafc; padding: 12px; border-radius: 6px; margin: 12px 0;">
                    <strong>📄 Source Files Used:</strong>
                    <div id="file-list">No files uploaded</div>
                </div>
                """,
                )

                # Action buttons
                with gr.Row():
                    copy_all_btn = gr.Button("📋 Copy All", variant="primary")
                    copy_code_btn = gr.Button("📝 Copy Code Blocks")
                    download_btn = gr.Button("💾 Download")
                    regenerate_btn = gr.Button("🔄 Regenerate")

                # Feedback section
                with gr.Row():
                    thumbs_up = gr.Button("👍", scale=1)
                    thumbs_down = gr.Button("👎", scale=1)
                    feedback_comment = gr.Textbox(
                        placeholder="Optional feedback comment...",
                        label="Feedback",
                        lines=1,
                        scale=4,
                    )

            # Event handlers
            def handle_enhancement(
                text_input,
                files,
                model_mode,
                custom_model,
                reasoning_depth,
                search_tier,
                temperature,
                session_state,
            ):
                """Handle the enhancement process with comprehensive security validation."""
                import os
                import time
                from pathlib import Path

                try:
                    # Initialize session if needed
                    if session_state.get("session_start_time") is None:
                        session_state["session_start_time"] = time.time()
                        session_state["session_id"] = f"session_{int(time.time() * 1000)}"  # Unique session ID

                    # 0. RATE LIMITING CHECK
                    session_id = session_state.get("session_id", "unknown")
                    if not self.rate_limiter.check_request_rate(session_id):
                        raise gr.Error(
                            "❌ Rate Limit Exceeded: Too many requests. "
                            "Please wait a moment before trying again. "
                            "Rate limits: 30 requests/minute, 200 requests/hour.",
                        )

                    if files and not self.rate_limiter.check_file_upload_rate(session_id):
                        raise gr.Error(
                            "❌ File Upload Rate Limit Exceeded: Too many file uploads. "
                            "Please wait before uploading more files. "
                            "Limit: 50 file uploads per hour.",
                        )

                    # 1. MODEL SELECTION VALIDATION
                    if not model_mode:
                        model_mode = "standard"  # Default fallback

                    if model_mode == "custom" and not custom_model:
                        custom_model = "gpt-4o-mini"  # Default fallback for custom mode

                    # Validate custom model selection
                    if custom_model and custom_model not in self.model_costs:
                        # Fallback to default if invalid model selected
                        self.logger.warning(f"Invalid model selected: {custom_model}, falling back to gpt-4o-mini")
                        custom_model = "gpt-4o-mini"

                    # 2. FILE COUNT VALIDATION
                    if files and len(files) > self.settings.max_files:
                        raise gr.Error(
                            f"❌ Security Error: Maximum {self.settings.max_files} files allowed. "
                            f"You uploaded {len(files)} files. Please reduce the number of files.",
                        )

                    # 3. FILE SIZE AND TYPE VALIDATION WITH MEMORY-SAFE PROCESSING
                    if files:
                        total_size = 0
                        processed_files = []

                        for file in files:
                            try:
                                # Get file info
                                if hasattr(file, "name") and file.name:
                                    file_path = file.name
                                    file_size = os.path.getsize(file_path)
                                    file_name = Path(file_path).name
                                    file_ext = Path(file_path).suffix.lower()

                                    # Size validation
                                    if file_size > self.settings.max_file_size:
                                        size_mb = file_size / (1024 * 1024)
                                        limit_mb = self.settings.max_file_size / (1024 * 1024)
                                        raise gr.Error(
                                            f"❌ Security Error: File '{file_name}' is {size_mb:.1f}MB, "
                                            f"which exceeds the {limit_mb:.0f}MB size limit. "
                                            f"Please upload a smaller file.",
                                        )

                                    # File type validation
                                    if file_ext not in self.settings.supported_file_types:
                                        supported_types = ", ".join(self.settings.supported_file_types)
                                        raise gr.Error(
                                            f"❌ Security Error: File '{file_name}' has unsupported type '{file_ext}'. "
                                            f"Supported types: {supported_types}",
                                        )

                                    # ENHANCED MIME type validation with content sniffing
                                    detected_mime, guessed_mime = self._validate_file_content_and_mime(
                                        file_path,
                                        file_ext,
                                    )
                                    if not self._is_safe_mime_type(
                                        detected_mime,
                                        file_ext,
                                    ) or not self._is_safe_mime_type(guessed_mime, file_ext):
                                        raise gr.Error(
                                            f"❌ Security Error: File '{file_name}' has suspicious content or MIME type. "
                                            f"Detected: '{detected_mime}', Expected for '{file_ext}'. "
                                            f"File may be corrupted, mislabeled, or potentially malicious.",
                                        )

                                    # MEMORY-SAFE FILE PROCESSING
                                    # Process files in chunks to prevent memory exhaustion
                                    file_content = self._process_file_safely(file_path, file_size)
                                    processed_files.append(
                                        {
                                            "name": file_name,
                                            "path": file_path,
                                            "size": file_size,
                                            "content": file_content,
                                            "type": file_ext,
                                        },
                                    )

                                    total_size += file_size

                            except OSError as e:
                                raise gr.Error(f"❌ File Error: Unable to access file. Error: {e!s}")

                        # Total size validation (additional safety check)
                        max_total_size = self.settings.max_file_size * self.settings.max_files
                        if total_size > max_total_size:
                            total_mb = total_size / (1024 * 1024)
                            limit_mb = max_total_size / (1024 * 1024)
                            raise gr.Error(
                                f"❌ Security Error: Total file size {total_mb:.1f}MB exceeds limit of {limit_mb:.0f}MB. "
                                f"Please reduce file sizes or upload fewer files.",
                            )

                        # Update files parameter with processed content for downstream processing
                        files = processed_files

                    # 4. TEXT INPUT VALIDATION
                    if text_input and len(text_input) > 50000:  # 50KB text limit
                        raise gr.Error(
                            f"❌ Input Error: Text input is too long ({len(text_input)} characters). "
                            f"Maximum 50,000 characters allowed. Please shorten your text.",
                        )

                    # 5. UPDATE SESSION TRACKING
                    session_state["request_count"] = session_state.get("request_count", 0) + 1

                    # Calculate estimated cost (mock calculation for now)
                    estimated_cost = self.model_costs.get(
                        custom_model if model_mode == "custom" else "gpt-4o-mini",
                        0.002,
                    )
                    session_state["total_cost"] = session_state.get("total_cost", 0.0) + estimated_cost

                    # 6. PROCESS WITH VALIDATED INPUTS AND COMPREHENSIVE ERROR HANDLING
                    try:
                        # Add timeout and processing constraints
                        import signal

                        def timeout_handler(signum, frame):
                            raise TimeoutError("Processing timeout exceeded")

                        # Set processing timeout (30 seconds)
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(30)

                        try:
                            result = journey1_processor.enhance_prompt(
                                text_input,
                                files,
                                model_mode,
                                custom_model,
                                reasoning_depth,
                                search_tier,
                                temperature,
                            )
                        finally:
                            # Always cancel timeout
                            signal.alarm(0)

                        # Validate result structure
                        if not result or len(result) < 9:
                            # Fallback to safe default result
                            result = self._create_fallback_result(text_input, custom_model)

                        # Return results with updated session state
                        return result + (session_state,)

                    except TimeoutError:
                        # Handle processing timeout
                        session_state["request_count"] = session_state.get("request_count", 0) + 1
                        session_state["total_cost"] = (
                            session_state.get("total_cost", 0.0) + 0.001
                        )  # Minimal cost for timeout

                        fallback_result = self._create_timeout_fallback_result(text_input, custom_model)
                        return fallback_result + (session_state,)

                    except Exception as processing_error:
                        # Handle processing errors with fallback
                        self.logger.error(f"Processing error: {processing_error}")
                        session_state["request_count"] = session_state.get("request_count", 0) + 1
                        session_state["total_cost"] = (
                            session_state.get("total_cost", 0.0) + 0.001
                        )  # Minimal cost for error

                        # Provide graceful degradation
                        fallback_result = self._create_error_fallback_result(
                            text_input,
                            custom_model,
                            str(processing_error),
                        )
                        return fallback_result + (session_state,)

                except gr.Error:
                    # Re-raise Gradio errors (these are user-facing)
                    raise
                except Exception as e:
                    # Log unexpected errors and show user-friendly message
                    self.logger.error(f"Unexpected error in file processing: {e}")
                    raise gr.Error(
                        "❌ Processing Error: An unexpected error occurred while processing your request. "
                        "Please try again or contact support if the problem persists.",
                    )

            def handle_copy_code(content):
                """Handle code block copying."""
                return journey1_processor.copy_code_blocks(content)

            def handle_copy_markdown(content):
                """Handle markdown copying."""
                return journey1_processor.copy_as_markdown(content)

            def handle_download(enhanced_prompt, context, request, examples, augmentations, tone_format, evaluation):
                """Handle download functionality."""
                create_breakdown = {
                    "context": context,
                    "request": request,
                    "examples": examples,
                    "augmentations": augmentations,
                    "tone_format": tone_format,
                    "evaluation": evaluation,
                }

                # Mock data for export
                model_info = {"model": "gpt-4o-mini", "response_time": 1.2, "cost": 0.003}
                file_sources = []
                session_data = {"total_cost": 0.003, "request_count": 1, "avg_response_time": 1.2}

                return export_utils.export_journey1_content(
                    enhanced_prompt,
                    create_breakdown,
                    model_info,
                    file_sources,
                    session_data,
                    "markdown",
                )

            def load_example():
                """Load example content."""
                return "Write a professional email to inform team members about a project delay. The delay is due to unexpected technical challenges with the database integration. We need to extend the deadline by 2 weeks and reassure the team that we're working on a solution."

            def clear_all():
                """Clear all inputs and outputs."""
                return ("", None, "", "", "", "", "", "", "", "")

            # Connect event handlers
            enhance_btn.click(
                fn=handle_enhancement,
                inputs=[
                    text_input,
                    file_upload,
                    model_selector,
                    custom_model_selector,
                    reasoning_depth,
                    search_tier,
                    temperature,
                    session_state,
                ],
                outputs=[
                    enhanced_prompt,
                    context_analysis,
                    request_specification,
                    examples_section,
                    augmentations_section,
                    tone_format,
                    evaluation_criteria,
                    model_attribution,
                    file_sources,
                    session_state,
                ],
            )

            copy_code_btn.click(fn=handle_copy_code, inputs=[enhanced_prompt], outputs=gr.Label(label="Copy Status"))

            copy_all_btn.click(fn=handle_copy_markdown, inputs=[enhanced_prompt], outputs=gr.Label(label="Copy Status"))

            download_btn.click(
                fn=handle_download,
                inputs=[
                    enhanced_prompt,
                    context_analysis,
                    request_specification,
                    examples_section,
                    augmentations_section,
                    tone_format,
                    evaluation_criteria,
                ],
                outputs=gr.File(label="Download"),
            )

            example_btn.click(fn=load_example, outputs=[text_input])

            clear_btn.click(
                fn=clear_all,
                outputs=[
                    text_input,
                    file_upload,
                    enhanced_prompt,
                    context_analysis,
                    request_specification,
                    examples_section,
                    augmentations_section,
                    tone_format,
                    evaluation_criteria,
                    file_sources,
                ],
            )

    def _create_journey2_interface(self):
        """Create Journey 2: Intelligent Search interface."""
        with gr.Column():
            gr.HTML(
                """
            <div class="journey-header">
                <div class="journey-title">Journey 2: Intelligent Search</div>
                <div class="journey-subtitle">HyDE-powered multi-source knowledge retrieval with context analysis</div>
            </div>
            """,
            )

            gr.Markdown("### 🔍 Search Interface")
            gr.HTML(
                "<p style='color: #64748b; font-style: italic;'>This interface will be implemented in the next phase as Journey 2 requires the HyDE processor and vector database integration.</p>",
            )

    def _create_journey3_interface(self):
        """Create Journey 3: IDE Integration interface."""
        with gr.Column():
            gr.HTML(
                """
            <div class="journey-header">
                <div class="journey-title">Journey 3: IDE Integration</div>
                <div class="journey-subtitle">AI-powered development with web-based VS Code through Code-Server</div>
            </div>
            """,
            )

            gr.Markdown("### 💻 Code-Server Integration")
            gr.HTML(
                "<p style='color: #64748b; font-style: italic;'>This interface will be implemented in the next phase as Journey 3 requires the Code-Server deployment and workspace integration.</p>",
            )

    def _create_journey4_interface(self):
        """Create Journey 4: Autonomous Workflows interface."""
        with gr.Column():
            gr.HTML(
                """
            <div class="journey-header">
                <div class="journey-title">Journey 4: Autonomous Workflows</div>
                <div class="journey-subtitle">Self-directed AI agents with comprehensive cost control and Free Mode</div>
            </div>
            """,
            )

            gr.Markdown("### 🤖 Workflow Management")
            gr.HTML(
                "<p style='color: #64748b; font-style: italic;'>This interface will be implemented in the next phase as Journey 4 requires the autonomous workflow engine and multi-agent coordination.</p>",
            )

    def _on_model_selector_change(self, model_mode: str) -> gr.Dropdown:
        """Handle model selector changes."""
        if model_mode == "custom":
            return gr.Dropdown(visible=True)
        return gr.Dropdown(visible=False)

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost for a model request."""
        if model not in self.model_costs:
            return 0.0

        cost_per_1k = self.model_costs[model]
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000) * cost_per_1k

    def update_session_cost(self, session_state: dict[str, Any], cost: float) -> None:
        """Update the session cost tracking for a specific user session."""
        session_state["total_cost"] = session_state.get("total_cost", 0.0) + cost

    def _validate_files(self, files: list[Any]) -> None:
        """
        Validate uploaded files for security and limits.

        Args:
            files: List of uploaded file objects

        Raises:
            gr.Error: If files exceed limits or contain security risks
        """
        if not files:
            return

        # Check file count limit
        if len(files) > self.settings.max_files:
            raise gr.Error(
                f"❌ Security Error: Maximum {self.settings.max_files} files allowed. "
                f"You uploaded {len(files)} files. Please reduce the number of files.",
            )

        for file_obj in files:
            file_path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
            file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
            file_ext = Path(file_path).suffix.lower()

            # Check file size limit
            if file_size > self.settings.max_file_size:
                size_mb = file_size / (1024 * 1024)
                limit_mb = self.settings.max_file_size / (1024 * 1024)
                raise gr.Error(
                    f"❌ Security Error: File '{Path(file_path).name}' is {size_mb:.1f}MB, "
                    f"which exceeds the {limit_mb:.0f}MB size limit. Please upload a smaller file.",
                )

            # Check file type
            if file_ext not in self.settings.supported_file_types:
                supported_types = ", ".join(self.settings.supported_file_types)
                raise gr.Error(
                    f"❌ Security Error: File '{Path(file_path).name}' has unsupported type '{file_ext}'. "
                    f"Supported types: {supported_types}",
                )

    def _validate_text_input(self, text_input: str) -> None:
        """
        Validate text input for length and security.

        Args:
            text_input: User text input

        Raises:
            gr.Error: If text input exceeds limits
        """
        if text_input and len(text_input) > 50000:  # 50KB text limit
            raise gr.Error(
                f"❌ Input Error: Text input is too long ({len(text_input)} characters). "
                f"Maximum 50,000 characters allowed. Please shorten your text.",
            )

    def _is_safe_mime_type(self, mime_type: str, file_ext: str) -> bool:
        """
        Validate that the MIME type matches the expected file extension.

        Args:
            mime_type: MIME type detected from file
            file_ext: File extension (with dot)

        Returns:
            True if MIME type is safe and matches extension
        """
        # Define safe MIME type mappings for supported file types
        safe_mime_mappings = {
            ".txt": ["text/plain", "text/x-log"],
            ".md": ["text/markdown", "text/plain", "text/x-markdown"],
            ".pdf": ["application/pdf"],
            ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
            ".csv": ["text/csv", "application/csv", "text/plain"],
            ".json": ["application/json", "text/json", "text/plain"],
        }

        allowed_mimes = safe_mime_mappings.get(file_ext.lower(), [])
        return mime_type in allowed_mimes if allowed_mimes else False

    def _validate_file_content_and_mime(self, file_path: str, file_ext: str) -> tuple[str, str]:
        """
        Validate file content using both magic number detection and MIME guessing.

        Args:
            file_path: Path to the file to validate
            file_ext: File extension for validation

        Returns:
            Tuple of (detected_mime_from_content, guessed_mime_from_extension)

        Raises:
            gr.Error: If content validation fails
        """
        try:
            import mimetypes

            import magic

            # Content-based MIME detection using magic numbers
            try:
                detected_mime = magic.from_file(file_path, mime=True)
            except Exception as e:
                self.logger.warning(f"Magic content detection failed: {e}")
                detected_mime = "application/octet-stream"  # Fallback for unknown content

            # Extension-based MIME guessing (existing method)
            guessed_mime, _ = mimetypes.guess_type(file_path)
            if not guessed_mime:
                guessed_mime = "application/octet-stream"

            # Additional security checks for common attack vectors
            self._check_for_content_anomalies(file_path, detected_mime, file_ext)

            return detected_mime, guessed_mime

        except ImportError:
            # Fallback if python-magic not available
            self.logger.warning("python-magic not available, falling back to basic MIME detection")
            import mimetypes

            guessed_mime, _ = mimetypes.guess_type(file_path)
            return guessed_mime or "application/octet-stream", guessed_mime or "application/octet-stream"
        except Exception as e:
            self.logger.error(f"File content validation failed: {e}")
            raise gr.Error(
                "❌ Security Error: Unable to validate file content safely. "
                "File may be corrupted or use unsupported format.",
            )

    def _check_for_content_anomalies(self, file_path: str, detected_mime: str, file_ext: str) -> None:
        """
        Check for content anomalies that might indicate malicious files.

        Args:
            file_path: Path to the file
            detected_mime: MIME type detected from content
            file_ext: File extension

        Raises:
            gr.Error: If anomalies are detected
        """
        # Check for polyglot files (files that are valid in multiple formats)
        suspicious_patterns = [
            # Archive formats in text files
            (detected_mime.startswith("application/zip"), file_ext in [".txt", ".md", ".csv", ".json"]),
            (detected_mime.startswith("application/x-tar"), file_ext in [".txt", ".md", ".csv", ".json"]),
            # Executable content in text files
            (detected_mime.startswith("application/x-executable"), file_ext in [".txt", ".md", ".csv", ".json"]),
            ("application/x-dosexec" in detected_mime, file_ext in [".txt", ".md", ".csv", ".json"]),
            # Script content in non-script files
            ("text/x-script" in detected_mime, file_ext not in [".txt", ".md"]),
        ]

        for condition, is_suspicious in suspicious_patterns:
            if condition and is_suspicious:
                raise gr.Error(
                    f"❌ Security Error: File appears to be a polyglot or contains suspicious content. "
                    f"Detected MIME type '{detected_mime}' is incompatible with extension '{file_ext}'. "
                    f"This may indicate a malicious file attempting to bypass security checks.",
                )

        # ENHANCEMENT 3: Archive bomb detection
        self._detect_archive_bombs(file_path, detected_mime)

    def _detect_archive_bombs(self, file_path: str, detected_mime: str) -> None:
        """
        Detect archive bombs (compression bombs) that could cause DoS through memory/disk exhaustion.

        Archive bombs are malicious files that are small when compressed but expand to huge sizes,
        potentially exhausting system resources when decompressed.

        Args:
            file_path: Path to the file to check
            detected_mime: MIME type detected from file content

        Raises:
            gr.Error: If archive bomb characteristics are detected
        """
        import os

        # Only check files that could be compressed archives
        archive_mimes = [
            "application/zip",
            "application/x-zip-compressed",
            "application/gzip",
            "application/x-gzip",
            "application/x-tar",
            "application/x-bzip2",
            "application/x-7z-compressed",
            "application/x-rar-compressed",
            "application/x-compress",
            "application/x-compressed",
        ]

        # Check if file appears to be an archive
        is_archive = any(archive_mime in detected_mime for archive_mime in archive_mimes)

        if is_archive:
            try:
                file_size = os.path.getsize(file_path)

                # Archive bomb heuristics
                self._check_archive_bomb_heuristics(file_path, file_size, detected_mime)

            except Exception as e:
                self.logger.warning(f"Archive bomb detection failed: {e}")
                # Fail safe - if we can't analyze, treat as suspicious
                raise gr.Error(
                    "❌ Security Error: Unable to analyze archive file safely. "
                    "For security reasons, this file cannot be processed.",
                )

    def _check_archive_bomb_heuristics(self, file_path: str, file_size: int, detected_mime: str) -> None:
        """
        Apply heuristics to detect potential archive bombs.

        Args:
            file_path: Path to the archive file
            file_size: Size of the compressed file
            detected_mime: MIME type of the file

        Raises:
            gr.Error: If archive bomb characteristics are detected
        """
        # Heuristic 1: Check compression ratio for common formats
        if "zip" in detected_mime:
            self._check_zip_bomb_heuristics(file_path, file_size)
        elif "gzip" in detected_mime or "tar" in detected_mime:
            self._check_tar_gzip_bomb_heuristics(file_path, file_size)

        # Heuristic 2: Size-based checks (regardless of format)
        # If a very small file claims to be an archive, it's suspicious
        if file_size < 100:  # Less than 100 bytes
            raise gr.Error(
                f"❌ Security Error: Archive file is suspiciously small ({file_size} bytes). "
                f"This could be an archive bomb designed to expand enormously when extracted.",
            )

    def _check_zip_bomb_heuristics(self, file_path: str, file_size: int) -> None:
        """
        Check for ZIP bomb characteristics using safe heuristics.

        Args:
            file_path: Path to the ZIP file
            file_size: Size of the ZIP file

        Raises:
            gr.Error: If ZIP bomb characteristics are detected
        """
        try:
            import zipfile

            # Safe limits for ZIP analysis
            MAX_FILES_TO_CHECK = 10
            MAX_UNCOMPRESSED_SIZE = 100 * 1024 * 1024  # 100MB total uncompressed
            MAX_COMPRESSION_RATIO = 1000  # 1000:1 compression ratio is suspicious

            with zipfile.ZipFile(file_path, "r") as zip_file:
                total_uncompressed = 0
                files_checked = 0

                for info in zip_file.filelist:
                    if files_checked >= MAX_FILES_TO_CHECK:
                        break

                    compressed_size = info.compress_size
                    uncompressed_size = info.file_size

                    # Check individual file compression ratio
                    if compressed_size > 0:  # Avoid division by zero
                        ratio = uncompressed_size / compressed_size
                        if ratio > MAX_COMPRESSION_RATIO:
                            raise gr.Error(
                                f"❌ Security Error: Archive contains file '{info.filename}' "
                                f"with suspicious compression ratio ({ratio:.0f}:1). "
                                f"This indicates a potential ZIP bomb attack.",
                            )

                    total_uncompressed += uncompressed_size
                    files_checked += 1

                    # Check if total uncompressed size is too large
                    if total_uncompressed > MAX_UNCOMPRESSED_SIZE:
                        raise gr.Error(
                            f"❌ Security Error: Archive would expand to {total_uncompressed / (1024*1024):.1f}MB. "
                            f"Maximum allowed expansion is {MAX_UNCOMPRESSED_SIZE / (1024*1024):.0f}MB. "
                            f"This could be an archive bomb.",
                        )

                # Overall compression ratio check
                if file_size > 0:
                    overall_ratio = total_uncompressed / file_size
                    if overall_ratio > MAX_COMPRESSION_RATIO:
                        raise gr.Error(
                            f"❌ Security Error: Archive has suspicious overall compression ratio "
                            f"({overall_ratio:.0f}:1). This indicates a potential archive bomb.",
                        )

        except zipfile.BadZipFile:
            raise gr.Error(
                "❌ Security Error: File appears to be a corrupted or malicious ZIP archive.",
            )
        except Exception as e:
            self.logger.warning(f"ZIP bomb detection failed: {e}")
            # Conservative approach - block if we can't safely analyze
            raise gr.Error(
                "❌ Security Error: Unable to safely analyze ZIP archive. File blocked as a security precaution.",
            )

    def _check_tar_gzip_bomb_heuristics(self, file_path: str, file_size: int) -> None:
        """
        Check for TAR/GZIP bomb characteristics using safe heuristics.

        Args:
            file_path: Path to the TAR/GZIP file
            file_size: Size of the compressed file

        Raises:
            gr.Error: If archive bomb characteristics are detected
        """
        try:
            import gzip
            import tarfile

            # Conservative limits for TAR/GZIP analysis
            MAX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024  # 50MB total uncompressed
            MAX_COMPRESSION_RATIO = 500  # 500:1 compression ratio limit

            # Try to analyze as tarfile first
            try:
                with tarfile.open(file_path, "r:*") as tar_file:
                    total_uncompressed = 0
                    files_checked = 0

                    for member in tar_file.getmembers():
                        if files_checked >= 10:  # Limit analysis to first 10 files
                            break

                        if member.isfile():
                            total_uncompressed += member.size
                            files_checked += 1

                            # Check if individual file is too large
                            if member.size > MAX_UNCOMPRESSED_SIZE:
                                raise gr.Error(
                                    f"❌ Security Error: Archive contains file '{member.name}' "
                                    f"that would expand to {member.size / (1024*1024):.1f}MB. "
                                    f"This could be an archive bomb.",
                                )

                    # Check overall expansion
                    if total_uncompressed > MAX_UNCOMPRESSED_SIZE:
                        raise gr.Error(
                            f"❌ Security Error: Archive would expand to {total_uncompressed / (1024*1024):.1f}MB. "
                            f"Maximum allowed is {MAX_UNCOMPRESSED_SIZE / (1024*1024):.0f}MB.",
                        )

                    # Check compression ratio
                    if file_size > 0:
                        ratio = total_uncompressed / file_size
                        if ratio > MAX_COMPRESSION_RATIO:
                            raise gr.Error(
                                f"❌ Security Error: Archive has suspicious compression ratio "
                                f"({ratio:.0f}:1). This indicates a potential archive bomb.",
                            )

            except tarfile.TarError:
                # If not a valid TAR, try GZIP
                with gzip.open(file_path, "rb") as gz_file:
                    # Read first chunk to estimate compression
                    chunk = gz_file.read(1024)  # Read 1KB sample
                    if len(chunk) == 1024:  # File has more content
                        # Estimate based on sample
                        estimated_uncompressed = file_size * 1000  # Conservative estimate
                        if estimated_uncompressed > MAX_UNCOMPRESSED_SIZE:
                            raise gr.Error(
                                "❌ Security Error: GZIP file appears to have excessive compression. "
                                "This could be a compression bomb.",
                            )

        except Exception as e:
            self.logger.warning(f"TAR/GZIP bomb detection failed: {e}")
            # Conservative approach - block if analysis fails
            raise gr.Error(
                "❌ Security Error: Unable to safely analyze compressed archive. "
                "File blocked as a security precaution.",
            )

    def _process_file_safely(self, file_path: str, file_size: int, chunk_size: int = 8192) -> str:
        """
        Process file content with memory bounds and streaming to prevent memory exhaustion.

        Args:
            file_path: Path to the file to process
            file_size: Size of the file in bytes
            chunk_size: Size of chunks to read (default 8KB)

        Returns:
            Processed file content as string

        Raises:
            gr.Error: If file processing fails or memory limits exceeded
        """
        try:
            # Memory limit: Don't load files larger than 5MB into memory at once
            memory_limit = 5 * 1024 * 1024  # 5MB

            if file_size > memory_limit:
                # For large files, read first chunk only and truncate
                with open(file_path, encoding="utf-8", errors="ignore") as file:
                    content_chunks = []
                    bytes_read = 0
                    # Reserve space for truncation message
                    truncation_msg = f"\n\n[FILE TRUNCATED - Original size: {file_size / (1024 * 1024):.1f}MB, showing first 5MB for memory safety]"
                    msg_size = len(truncation_msg.encode("utf-8"))
                    effective_limit = memory_limit - msg_size

                    current_content_size = 0
                    while current_content_size < effective_limit:
                        chunk = file.read(chunk_size)
                        if not chunk:
                            break

                        # Check if adding this chunk would exceed limit
                        chunk_size_bytes = len(chunk.encode("utf-8"))
                        if current_content_size + chunk_size_bytes > effective_limit:
                            # Take only part of the chunk that fits
                            remaining_bytes = effective_limit - current_content_size
                            # Approximate character count that fits in remaining bytes
                            partial_chars = int(remaining_bytes / (chunk_size_bytes / len(chunk)))
                            chunk = chunk[:partial_chars]

                        content_chunks.append(chunk)
                        current_content_size += len(chunk.encode("utf-8"))

                        # If we've hit our limit, stop
                        if current_content_size >= effective_limit:
                            break

                    content = "".join(content_chunks)

                    # Add truncation notice if file was truncated
                    if current_content_size >= effective_limit:
                        content += truncation_msg

                    return content
            else:
                # For smaller files, read normally but with error handling
                with open(file_path, encoding="utf-8", errors="ignore") as file:
                    return file.read()

        except UnicodeDecodeError:
            # Handle binary or non-text files
            raise gr.Error(
                "❌ File Error: File appears to be binary or uses unsupported encoding. "
                "Please ensure file is in UTF-8 text format.",
            )
        except MemoryError:
            # Handle memory exhaustion
            raise gr.Error(
                "❌ Memory Error: File is too large to process safely. "
                "Please upload a smaller file (under 5MB recommended).",
            )
        except OSError as e:
            # Handle file system errors
            raise gr.Error(f"❌ File Error: Unable to read file. {e!s}")
        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error processing file {file_path}: {e}")
            raise gr.Error(
                "❌ Processing Error: Unable to process file safely. Please try again or contact support.",
            )

    def _create_fallback_result(self, text_input: str, model: str) -> tuple:
        """Create fallback result when normal processing fails."""
        fallback_prompt = f"""
**Enhanced Prompt (Fallback Mode)**

Your original input: {text_input[:500]}{"..." if len(text_input) > 500 else ""}

**Note**: The advanced enhancement system is temporarily unavailable. Here's a basic structure to help you proceed:

## Context
Please provide more context about your specific goals and requirements.

## Request
{text_input[:200]}{"..." if len(text_input) > 200 else ""}

## Suggested Next Steps
1. Clarify your specific objectives
2. Define success criteria
3. Consider any constraints or requirements
4. Try the enhancement again when the system is available

---
*Fallback mode active - basic prompt structure provided*
"""

        return (
            fallback_prompt,  # enhanced_prompt
            "Basic context analysis - please specify your role and goals",  # context_analysis
            f"Request: {text_input[:100]}{'...' if len(text_input) > 100 else ''}",  # request_specification
            "Examples will be provided when system is fully available",  # examples_section
            "Advanced frameworks temporarily unavailable",  # augmentations_section
            "Please specify your preferred tone and format",  # tone_format
            "Success criteria: Define what good output looks like",  # evaluation_criteria
            f'<div class="model-attribution"><strong>🤖 Fallback Mode:</strong> {model} | <strong>⚠️ Status:</strong> Limited functionality</div>',  # model_attribution
            '<div id="file-sources">Fallback mode - file processing limited</div>',  # file_sources
        )

    def _create_timeout_fallback_result(self, text_input: str, model: str) -> tuple:
        """Create fallback result when processing times out."""
        timeout_prompt = f"""
**Enhanced Prompt (Timeout Recovery)**

Your request: {text_input[:300]}{"..." if len(text_input) > 300 else ""}

**⏱️ Processing Timeout Notice**: Your request is complex and requires more processing time than currently available.

## Simplified Approach
To get faster results, try:
1. **Shorter inputs**: Break complex requests into smaller parts
2. **Specific focus**: Target one main objective at a time
3. **Clear context**: Provide essential background only

## Quick Enhancement
Your core request appears to be: {text_input[:150]}{"..." if len(text_input) > 150 else ""}

Consider refining this to be more specific and actionable.

---
*Timeout recovery mode - please simplify your request for faster processing*
"""

        return (
            timeout_prompt,  # enhanced_prompt
            "⏱️ Timeout - please provide more focused context",  # context_analysis
            f"Simplified request needed: {text_input[:100]}{'...' if len(text_input) > 100 else ''}",  # request_specification
            "⏱️ Examples unavailable due to timeout - try simpler request",  # examples_section
            "⏱️ Advanced processing unavailable - reduce complexity",  # augmentations_section
            "Suggest concise, direct communication style",  # tone_format
            "Success: Faster response with simpler, focused request",  # evaluation_criteria
            f'<div class="model-attribution"><strong>⏱️ Timeout Recovery:</strong> {model} | <strong>🔄 Suggestion:</strong> Simplify request</div>',  # model_attribution
            '<div id="file-sources">⏱️ File processing timeout - try fewer/smaller files</div>',  # file_sources
        )

    def _create_error_fallback_result(self, text_input: str, model: str, error_msg: str) -> tuple:
        """Create fallback result when processing encounters an error."""
        error_prompt = f"""
**Enhanced Prompt (Error Recovery)**

Your input: {text_input[:250]}{"..." if len(text_input) > 250 else ""}

**🔧 System Recovery Mode**: An error occurred during processing, but we've created this basic enhancement to help you proceed.

## Basic Structure
**Objective**: {text_input[:100]}{"..." if len(text_input) > 100 else ""}

**Recommended approach**:
1. Define clear, specific goals
2. Provide necessary context
3. Specify desired outcome format
4. Include any important constraints

## Troubleshooting
If this error persists:
- Try shorter, simpler inputs
- Check file formats and sizes
- Contact support if needed

---
*Error recovery mode - basic assistance provided*
"""

        return (
            error_prompt,  # enhanced_prompt
            "🔧 Error recovery - basic context structure provided",  # context_analysis
            f"Core request: {text_input[:100]}{'...' if len(text_input) > 100 else ''}",  # request_specification
            "🔧 Examples temporarily unavailable - error recovery mode",  # examples_section
            "🔧 Advanced features unavailable - contact support if persistent",  # augmentations_section
            "Clear, direct communication recommended",  # tone_format
            "Success: Error resolved and normal functionality restored",  # evaluation_criteria
            f'<div class="model-attribution"><strong>🔧 Error Recovery:</strong> {model} | <strong>📧 Support:</strong> help@promptcraft.ai</div>',  # model_attribution
            '<div id="file-sources">🔧 Error recovery mode - file processing affected</div>',  # file_sources
        )


def create_app() -> gr.Blocks:
    """Create and return the Gradio application."""
    interface = MultiJourneyInterface()
    return interface.create_interface()


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False, debug=True)
