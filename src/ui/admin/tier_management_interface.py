"""Admin Interface for User Tier Management.

This module provides Gradio interface components for administrators to manage
user tier assignments, view user statistics, and monitor system configuration.
"""

import logging

import gradio as gr
import pandas as pd
from typing import Any

from src.admin.user_tier_manager import UserTierManager


logger = logging.getLogger(__name__)


class TierManagementInterface:
    """Gradio interface for user tier management."""

    def __init__(self) -> None:
        """Initialize the tier management interface."""
        self.tier_manager = UserTierManager()

    def create_admin_interface(self) -> gr.Tab:
        """Create the admin tab for user tier management.

        Returns:
            Gradio Tab component with admin interface
        """
        with gr.Tab("👑 Admin: User Management", visible=False, elem_id="admin-tab") as admin_tab:

            gr.HTML(
                """
                <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                    <h3 style="color: #dc2626; margin: 0 0 8px 0;">🔒 Administrator Access Only</h3>
                    <p style="color: #dc2626; margin: 0; font-size: 14px;">
                        This interface allows you to manage user tier assignments. Changes affect model access permissions.
                        <strong>Use responsibly and verify changes before applying.</strong>
                    </p>
                </div>
            """,
            )

            with gr.Row():
                # Left Column - User Management
                with gr.Column(scale=2):
                    gr.HTML("<h3>👥 User Tier Management</h3>")

                    # User Assignment Section
                    with gr.Group():
                        gr.HTML("<h4>Assign User Tier</h4>")

                        with gr.Row():
                            user_email_input = gr.Textbox(
                                label="Email Address",
                                placeholder="user@example.com or @domain.com",
                                elem_id="user-email-input",
                            )
                            tier_selection = gr.Dropdown(
                                label="Tier Assignment",
                                choices=[
                                    ("👑 Admin (Full Access + Admin Features)", "admin"),
                                    ("⭐ Full User (All Models)", "full"),
                                    ("🔒 Limited User (Free Models Only)", "limited"),
                                ],
                                value="limited",
                                elem_id="tier-selection",
                            )

                        with gr.Row():
                            assign_button = gr.Button("Assign Tier", variant="primary", elem_id="assign-tier-btn")
                            remove_button = gr.Button(
                                "Remove from All Tiers",
                                variant="secondary",
                                elem_id="remove-tier-btn",
                            )

                    # Assignment Result
                    assignment_result = gr.HTML(elem_id="assignment-result")

                    # Bulk Assignment Section
                    with gr.Group():
                        gr.HTML("<h4>Bulk Assignment</h4>")

                        bulk_emails = gr.Textbox(
                            label="Email List (one per line)",
                            placeholder="user1@example.com\nuser2@example.com\n@company.com",
                            lines=5,
                            elem_id="bulk-emails",
                        )

                        with gr.Row():
                            bulk_tier = gr.Dropdown(
                                label="Bulk Tier Assignment",
                                choices=[("⭐ Full User", "full"), ("🔒 Limited User", "limited")],
                                value="limited",
                            )
                            bulk_assign_button = gr.Button("Bulk Assign", variant="secondary")

                    bulk_result = gr.HTML(elem_id="bulk-result")

                # Right Column - User Display and Stats
                with gr.Column(scale=3):
                    gr.HTML("<h3>📊 User Overview</h3>")

                    # Search and Filter
                    with gr.Row():
                        search_input = gr.Textbox(
                            label="Search Users",
                            placeholder="Search by email...",
                            elem_id="user-search",
                        )
                        search_button = gr.Button("Search", variant="secondary")
                        refresh_button = gr.Button("Refresh All", variant="secondary")

                    # User Statistics
                    stats_display = gr.HTML(elem_id="stats-display")

                    # User Tables by Tier
                    with gr.Tab("Admin Users"):
                        admin_users_df = gr.Dataframe(
                            headers=["Email", "Access Level", "Status"],
                            elem_id="admin-users-table",
                            interactive=False,
                        )

                    with gr.Tab("Full Users"):
                        full_users_df = gr.Dataframe(
                            headers=["Email", "Access Level", "Status"],
                            elem_id="full-users-table",
                            interactive=False,
                        )

                    with gr.Tab("Limited Users"):
                        limited_users_df = gr.Dataframe(
                            headers=["Email", "Access Level", "Status"],
                            elem_id="limited-users-table",
                            interactive=False,
                        )

                    with gr.Tab("Unassigned"):
                        unassigned_df = gr.Dataframe(
                            headers=["Email", "Status", "Note"],
                            elem_id="unassigned-table",
                            interactive=False,
                        )

            # Configuration and Logs Section
            with gr.Row(), gr.Column():
                gr.HTML("<h3>⚙️ Configuration Management</h3>")

                with gr.Row():
                    validate_config_button = gr.Button("Validate Configuration", variant="secondary")
                    export_config_button = gr.Button("Export Configuration", variant="secondary")
                    persist_changes_button = gr.Button("Apply Changes", variant="primary")

                with gr.Row():
                    reload_config_button = gr.Button("Reload from Environment", variant="secondary")
                    generate_env_button = gr.Button("Generate .env Updates", variant="secondary")

                config_status = gr.HTML(elem_id="config-status")

                # Changes Log
                with gr.Group():
                    gr.HTML("<h4>Recent Changes</h4>")
                    changes_log = gr.Textbox(
                        label="Activity Log",
                        lines=10,
                        elem_id="changes-log",
                        interactive=False,
                    )
                    refresh_log_button = gr.Button("Refresh Log", variant="secondary")

            # Event Handlers
            self._setup_event_handlers(
                assign_button=assign_button,
                remove_button=remove_button,
                bulk_assign_button=bulk_assign_button,
                search_button=search_button,
                refresh_button=refresh_button,
                validate_config_button=validate_config_button,
                export_config_button=export_config_button,
                persist_changes_button=persist_changes_button,
                reload_config_button=reload_config_button,
                generate_env_button=generate_env_button,
                refresh_log_button=refresh_log_button,
                user_email_input=user_email_input,
                tier_selection=tier_selection,
                assignment_result=assignment_result,
                bulk_emails=bulk_emails,
                bulk_tier=bulk_tier,
                bulk_result=bulk_result,
                search_input=search_input,
                stats_display=stats_display,
                admin_users_df=admin_users_df,
                full_users_df=full_users_df,
                limited_users_df=limited_users_df,
                unassigned_df=unassigned_df,
                config_status=config_status,
                changes_log=changes_log,
            )

        return admin_tab  # type: ignore[no-any-return]

    def _setup_event_handlers(self, **components: Any) -> None:
        """Setup event handlers for all components."""

        # Assign tier button
        components["assign_button"].click(
            fn=self._assign_tier,
            inputs=[components["user_email_input"], components["tier_selection"]],
            outputs=[
                components["assignment_result"],
                components["stats_display"],
                *self._get_table_outputs(components),
            ],
        )

        # Remove tier button
        components["remove_button"].click(
            fn=self._remove_tier,
            inputs=[components["user_email_input"]],
            outputs=[
                components["assignment_result"],
                components["stats_display"],
                *self._get_table_outputs(components),
            ],
        )

        # Bulk assign button
        components["bulk_assign_button"].click(
            fn=self._bulk_assign,
            inputs=[components["bulk_emails"], components["bulk_tier"]],
            outputs=[components["bulk_result"], components["stats_display"], *self._get_table_outputs(components)],
        )

        # Search button
        components["search_button"].click(
            fn=self._search_users,
            inputs=[components["search_input"]],
            outputs=[components["stats_display"], *self._get_table_outputs(components)],
        )

        # Refresh button
        components["refresh_button"].click(
            fn=self._refresh_all_data,
            outputs=[components["stats_display"], *self._get_table_outputs(components)],
        )

        # Validate config button
        components["validate_config_button"].click(
            fn=self._validate_configuration,
            outputs=[components["config_status"]],
        )

        # Export config button
        components["export_config_button"].click(fn=self._export_configuration, outputs=[components["config_status"]])

        # Persist changes button
        components["persist_changes_button"].click(fn=self._persist_changes, outputs=[components["config_status"]])

        # Reload config button
        components["reload_config_button"].click(
            fn=self._reload_configuration,
            outputs=[components["config_status"], components["stats_display"], *self._get_table_outputs(components)],
        )

        # Generate env button
        components["generate_env_button"].click(fn=self._generate_env_updates, outputs=[components["config_status"]])

        # Refresh log button
        components["refresh_log_button"].click(fn=self._refresh_changes_log, outputs=[components["changes_log"]])

    def _get_table_outputs(self, components: dict[str, Any]) -> list[gr.Component]:
        """Get list of table components for outputs."""
        return [
            components["admin_users_df"],
            components["full_users_df"],
            components["limited_users_df"],
            components["unassigned_df"],
        ]

    def _assign_tier(
        self,
        email: str,
        tier: str,
    ) -> tuple[str, str, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Assign user to tier."""
        try:
            # Get admin email from request context (this would be injected by middleware)
            admin_email = "admin@example.com"  # TODO: Get from request context

            success, message = self.tier_manager.assign_user_tier(email, tier, admin_email)

            if success:
                result_html = f"""
                    <div style="background: #dcfce7; border: 1px solid #16a34a; border-radius: 6px; padding: 12px; margin: 8px 0;">
                        <strong style="color: #15803d;">✅ Success:</strong> {message}
                    </div>
                """
            else:
                result_html = f"""
                    <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 6px; padding: 12px; margin: 8px 0;">
                        <strong style="color: #dc2626;">❌ Error:</strong> {message}
                    </div>
                """

            stats_html = self._generate_stats_html()
            tables = self._generate_user_tables()

            return (result_html, stats_html, *tables)

        except Exception as e:
            logger.error("Error in assign_tier: %s", e)
            error_html = f"""
                <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 6px; padding: 12px; margin: 8px 0;">
                    <strong style="color: #dc2626;">❌ System Error:</strong> {e!s}
                </div>
            """
            return (error_html, "", pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    def _remove_tier(self, email: str) -> tuple[str, str, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Remove user from all tiers."""
        try:
            admin_email = "admin@example.com"  # TODO: Get from request context

            success, message = self.tier_manager.remove_user_tier(email, admin_email)

            if success:
                result_html = f"""
                    <div style="background: #dcfce7; border: 1px solid #16a34a; border-radius: 6px; padding: 12px; margin: 8px 0;">
                        <strong style="color: #15803d;">✅ Success:</strong> {message}
                    </div>
                """
            else:
                result_html = f"""
                    <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 6px; padding: 12px; margin: 8px 0;">
                        <strong style="color: #dc2626;">❌ Error:</strong> {message}
                    </div>
                """

            stats_html = self._generate_stats_html()
            tables = self._generate_user_tables()

            return (result_html, stats_html, *tables)

        except Exception as e:
            logger.error("Error in remove_tier: %s", e)
            return (f"System error: {e!s}", "", pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    def _bulk_assign(
        self,
        emails_text: str,
        tier: str,
    ) -> tuple[str, str, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Bulk assign users to tier."""
        try:
            if not emails_text.strip():
                return (
                    "Please enter email addresses",
                    "",
                    pd.DataFrame(),
                    pd.DataFrame(),
                    pd.DataFrame(),
                    pd.DataFrame(),
                )

            emails = [email.strip() for email in emails_text.strip().split("\n") if email.strip()]
            admin_email = "admin@example.com"  # TODO: Get from request context

            results = self.tier_manager.bulk_assign_tier(emails, tier, admin_email)

            result_html = f"""
                <div style="background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 6px; padding: 12px; margin: 8px 0;">
                    <h4 style="color: #0c4a6e; margin: 0 0 8px 0;">Bulk Assignment Results</h4>
                    <p style="margin: 4px 0; color: #0c4a6e;">
                        <strong>Total:</strong> {results['total']} |
                        <strong>Successful:</strong> {len(results['successful'])} |
                        <strong>Failed:</strong> {len(results['failed'])}
                    </p>
            """

            if results["failed"]:
                result_html += "<h5 style='color: #dc2626; margin: 8px 0 4px 0;'>Failed:</h5><ul style='margin: 0; color: #dc2626;'>"
                for failure in results["failed"][:10]:  # Show first 10 failures
                    result_html += f"<li>{failure['email']}: {failure['error']}</li>"
                result_html += "</ul>"

            result_html += "</div>"

            stats_html = self._generate_stats_html()
            tables = self._generate_user_tables()

            return (result_html, stats_html, *tables)

        except Exception as e:
            logger.error("Error in bulk_assign: %s", e)
            return (f"System error: {e!s}", "", pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    def _search_users(self, query: str) -> tuple[str, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Search users."""
        try:
            if not query.strip():
                return self._refresh_all_data()

            matching_users = self.tier_manager.search_users(query.strip())

            stats_html = f"""
                <div style="background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 6px; padding: 12px; margin: 8px 0;">
                    <h4 style="color: #0c4a6e; margin: 0;">Search Results</h4>
                    <p style="color: #0c4a6e; margin: 8px 0 0 0;">Found {len(matching_users)} users matching "{query}"</p>
                </div>
            """

            # Organize search results by tier
            search_results: dict[str, list[Any]] = {"admin": [], "full": [], "limited": [], "unassigned": []}
            for user in matching_users:
                search_results[user["current_tier"]].append(user)

            tables = self._generate_tables_from_data(search_results)

            return (stats_html, *tables)

        except Exception as e:
            logger.error("Error in search_users: %s", e)
            return (f"Search error: {e!s}", pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    def _refresh_all_data(self) -> tuple[str, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Refresh all user data and statistics."""
        try:
            stats_html = self._generate_stats_html()
            tables = self._generate_user_tables()
            return (stats_html, *tables)

        except Exception as e:
            logger.error("Error refreshing data: %s", e)
            return (f"Refresh error: {e!s}", pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    def _validate_configuration(self) -> str:
        """Validate current configuration."""
        try:
            warnings = self.tier_manager.validate_tier_configuration()

            if not warnings:
                return """
                    <div style="background: #dcfce7; border: 1px solid #16a34a; border-radius: 6px; padding: 12px;">
                        <strong style="color: #15803d;">✅ Configuration Valid</strong>
                        <p style="color: #15803d; margin: 8px 0 0 0;">No configuration issues detected.</p>
                    </div>
                """
            warnings_html = "<ul style='margin: 8px 0 0 0; color: #ea580c;'>"
            for warning in warnings:
                warnings_html += f"<li>{warning}</li>"
            warnings_html += "</ul>"

            return f"""
                    <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px; padding: 12px;">
                        <strong style="color: #92400e;">⚠️ Configuration Warnings</strong>
                        {warnings_html}
                    </div>
                """

        except Exception as e:
            logger.error("Error validating configuration: %s", e)
            return f"""
                <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 6px; padding: 12px;">
                    <strong style="color: #dc2626;">❌ Validation Error:</strong> {e!s}
                </div>
            """

    def _export_configuration(self) -> str:
        """Export current configuration."""
        try:
            config_json = self.tier_manager.export_tier_configuration()

            return f"""
                <div style="background: #dcfce7; border: 1px solid #16a34a; border-radius: 6px; padding: 12px;">
                    <strong style="color: #15803d;">✅ Configuration Exported</strong>
                    <details style="margin-top: 8px;">
                        <summary style="color: #15803d; cursor: pointer;">View Configuration JSON</summary>
                        <pre style="background: #f8f9fa; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 12px; margin-top: 8px;">{config_json}</pre>
                    </details>
                </div>
            """

        except Exception as e:
            logger.error("Error exporting configuration: %s", e)
            return f"""
                <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 6px; padding: 12px;">
                    <strong style="color: #dc2626;">❌ Export Error:</strong> {e!s}
                </div>
            """

    def _refresh_changes_log(self) -> str:
        """Refresh changes log."""
        try:
            changes = self.tier_manager.get_changes_log(50)

            if not changes:
                return "No recent changes recorded."

            log_text = ""
            for change in reversed(changes):  # Most recent first
                timestamp = change["timestamp"][:19].replace("T", " ")
                log_text += f"[{timestamp}] {change['action'].upper()}: {change['email']}"
                if "tier" in change:
                    log_text += f" -> {change['tier']}"
                log_text += f" (by {change['admin']})\n"

            return log_text

        except Exception as e:
            logger.error("Error refreshing changes log: %s", e)
            return f"Error loading changes log: {e!s}"

    def _persist_changes(self) -> str:
        """Persist tier configuration changes."""
        try:
            success, message = self.tier_manager.persist_changes()

            if success:
                return f"""
                    <div style="background: #dcfce7; border: 1px solid #16a34a; border-radius: 6px; padding: 12px;">
                        <strong style="color: #15803d;">✅ Changes Applied</strong>
                        <p style="color: #15803d; margin: 8px 0 0 0;">{message}</p>
                    </div>
                """
            return f"""
                    <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 6px; padding: 12px;">
                        <strong style="color: #dc2626;">❌ Persistence Error:</strong> {message}
                    </div>
                """

        except Exception as e:
            logger.error("Error persisting changes: %s", e)
            return f"""
                <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 6px; padding: 12px;">
                    <strong style="color: #dc2626;">❌ System Error:</strong> {e!s}
                </div>
            """

    def _reload_configuration(self) -> tuple[str, str, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Reload configuration from environment."""
        try:
            success, message = self.tier_manager.reload_configuration()

            if success:
                status_html = f"""
                    <div style="background: #dcfce7; border: 1px solid #16a34a; border-radius: 6px; padding: 12px;">
                        <strong style="color: #15803d;">✅ Configuration Reloaded</strong>
                        <p style="color: #15803d; margin: 8px 0 0 0;">{message}</p>
                    </div>
                """
            else:
                status_html = f"""
                    <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 6px; padding: 12px;">
                        <strong style="color: #dc2626;">❌ Reload Error:</strong> {message}
                    </div>
                """

            # Refresh data after reload
            stats_html = self._generate_stats_html()
            tables = self._generate_user_tables()

            return (status_html, stats_html, *tables)

        except Exception as e:
            logger.error("Error reloading configuration: %s", e)
            error_html = f"""
                <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 6px; padding: 12px;">
                    <strong style="color: #dc2626;">❌ System Error:</strong> {e!s}
                </div>
            """
            return (error_html, "", pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    def _generate_env_updates(self) -> str:
        """Generate environment file updates."""
        try:
            env_content = self.tier_manager.generate_env_file_updates()

            return f"""
                <div style="background: #dcfce7; border: 1px solid #16a34a; border-radius: 6px; padding: 12px;">
                    <strong style="color: #15803d;">✅ Environment Updates Generated</strong>
                    <details style="margin-top: 8px;">
                        <summary style="color: #15803d; cursor: pointer;">View Environment File Updates</summary>
                        <div style="margin-top: 8px;">
                            <p style="color: #15803d; font-size: 14px; margin-bottom: 8px;">
                                Copy these lines to your .env file and restart the application:
                            </p>
                            <pre style="background: #f8f9fa; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 12px; border: 1px solid #e2e8f0;">{env_content}</pre>
                        </div>
                    </details>
                </div>
            """

        except Exception as e:
            logger.error("Error generating env updates: %s", e)
            return f"""
                <div style="background: #fee2e2; border: 1px solid #dc2626; border-radius: 6px; padding: 12px;">
                    <strong style="color: #dc2626;">❌ Generation Error:</strong> {e!s}
                </div>
            """

    def _generate_stats_html(self) -> str:
        """Generate HTML for statistics display."""
        try:
            stats = self.tier_manager.get_tier_statistics()

            return f"""
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 8px 0;">
                    <h4 style="margin: 0 0 12px 0; color: #374151;">📊 User Statistics</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div>
                            <p style="margin: 4px 0;"><strong>👑 Admin Users:</strong> {stats.get('tier_distribution', {}).get('admin', 0)}</p>
                            <p style="margin: 4px 0;"><strong>⭐ Full Users:</strong> {stats.get('tier_distribution', {}).get('full', 0)}</p>
                            <p style="margin: 4px 0;"><strong>🔒 Limited Users:</strong> {stats.get('tier_distribution', {}).get('limited', 0)}</p>
                        </div>
                        <div>
                            <p style="margin: 4px 0;"><strong>Total Authorized:</strong> {stats.get('total_authorized_users', 0)}</p>
                            <p style="margin: 4px 0;"><strong>Whitelist Entries:</strong> {stats.get('individual_emails', 0)}</p>
                            <p style="margin: 4px 0;"><strong>Domain Patterns:</strong> {len(stats.get('domains', []))}</p>
                        </div>
                    </div>
                </div>
            """

        except Exception as e:
            logger.error("Error generating stats HTML: %s", e)
            return f"<div>Error loading statistics: {e!s}</div>"

    def _generate_user_tables(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate user tables for all tiers."""
        try:
            users_by_tier = self.tier_manager.get_all_users()
            return self._generate_tables_from_data(users_by_tier)

        except Exception as e:
            logger.error("Error generating user tables: %s", e)
            return (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    def _generate_tables_from_data(
        self,
        users_by_tier: dict[str, list],
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate DataFrames from user data."""

        # Admin users table
        admin_data = []
        for user in users_by_tier.get("admin", []):
            admin_data.append([user["email"], "Full Access + Admin", "✅ Active"])
        admin_df = pd.DataFrame(admin_data, columns=["Email", "Access Level", "Status"])

        # Full users table
        full_data = []
        for user in users_by_tier.get("full", []):
            full_data.append([user["email"], "All Models", "✅ Active"])
        full_df = pd.DataFrame(full_data, columns=["Email", "Access Level", "Status"])

        # Limited users table
        limited_data = []
        for user in users_by_tier.get("limited", []):
            limited_data.append([user["email"], "Free Models Only", "✅ Active"])
        limited_df = pd.DataFrame(limited_data, columns=["Email", "Access Level", "Status"])

        # Unassigned users table
        unassigned_data = []
        for user in users_by_tier.get("unassigned", []):
            unassigned_data.append([user["email"], "No Tier Assigned", "⚠️ Defaults to Limited"])
        unassigned_df = pd.DataFrame(unassigned_data, columns=["Email", "Status", "Note"])

        return admin_df, full_df, limited_df, unassigned_df
