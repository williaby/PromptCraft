---
title: CREATE Framework Summary and Compliance Evaluation
version: 1.0
status: draft
agent_id: create_agent
tags: ['create', 'framework', 'evaluation', 'prompt_engineering', 'compliance']
purpose: Comprehensive summary of the CREATE framework structure, components, and compliance evaluation guidelines.
---

# CREATE Framework Summary and Compliance Evaluation

## Overview of the CREATE Framework

The C.R.E.A.T.E. Framework is a comprehensive prompt engineering methodology designed to transform queries into accurate, context-aware outputs through structured, multi-component prompts. It serves as the core methodology for PromptCraft Pro, enabling systematic construction of high-quality AI prompts.

### Core Philosophy

The framework operates on the principle that effective AI prompting requires methodical construction across six distinct components, each building upon the previous to create increasingly sophisticated and reliable outputs. The framework emphasizes precision, accountability, and systematic evaluation to minimize hallucinations and maximize output quality.

## Framework Components

### C - Context (Role, Background, Goal)

**Purpose**: Establishes the foundational identity, knowledge base, and objective for the AI response.

**Key Elements**:
- **Role and Persona Clause**: Defines the AI's professional identity using 3-5 core tokens plus a ≤12-word humanizing detail
  - Template: "You are a `<ROLE core>`, `<persona clause>`"
  - Example: "You are a senior counsel, specializing in Oregon tax litigation"
- **Background Information**: Provides essential contextual knowledge about the specific subject matter
- **Goal/Intent**: Clarifies the ultimate purpose and desired impact of the output

**Critical Requirements**:
- Never use AI/LLM/chatbot references in role definitions
- Place role definition first to prime domain tokens early
- Avoid parentheses or brand IDs in persona clauses

### R - Request (Task, Format, Depth, Action Verbs)

**Purpose**: Articulates the precise deliverable requirements and specifications.

**Key Elements**:
- **Deliverable and Format**: Explicit specification of output type and structure
- **Depth and Length Control**: Uses established 10-tier system from "Nano Answer" (≤60 words) to "Max-Window Synthese" (50,000+ words)
- **Action Verbs**: Specific, strong verbs that define the cognitive task (analyze, synthesize, evaluate, etc.)

**Depth Tiers** (Key Examples):
- Tier 1: Nano (≤60 words) - One-liner responses
- Tier 4: Overview (400-900 words) - Analyst orientation  
- Tier 6: In-Depth Analysis (2000-5000 words) - White paper/memo
- Tier 10: Max-Window Synthese (50,000+ words) - Book-length manuscript

### E - Examples (Few-Shot Prompting)

**Purpose**: Provides concrete demonstrations of desired output format, style, and reasoning patterns.

**Key Elements**:
- **Few-Shot Learning**: 1-3 well-chosen examples that demonstrate the exact pattern desired
- **Clear Delimiters**: Structured separation using markers like `### Example ###`
- **Format Consistency**: Examples must perfectly match desired output quality and style

**When to Use**:
- Critical formatting requirements (JSON, specific citation styles)
- Nuanced tone or style requirements
- Complex or novel tasks requiring demonstration
- Consistency across multiple runs

### A - Augmentations (Frameworks, Evidence, Reasoning)

**Purpose**: Adds sophisticated analytical rigor and evidence grounding to the request.

**Key Components**:
- **Analytical Frameworks**: Invokes established methodologies (SWOT, IRAC, CBA, STRIDE, etc.)
- **Evidence Specification**: Mandates specific sources and citation requirements
- **Live Data Integration**: Uses `web.search_query` with recency filters for volatile information
- **Advanced Reasoning Modes**: Chain-of-Thought, Tree-of-Thought, and specialized evaluation techniques

**Framework Library** (Selected Examples):
- **SWOT Analysis**: Four quadrants for strategic planning
- **IRAC/CREAC**: Legal analysis structure (Issue → Rule → Application → Conclusion)
- **STRIDE**: Security threat modeling (Spoofing, Tampering, Repudiation, etc.)
- **Cost-Benefit Analysis**: NPV and sensitivity analysis for fiscal decisions

### T - Tone & Format (Voice, Style, Structure)

**Purpose**: Defines presentation style, rhetorical devices, and structural formatting.

**Key Elements**:
- **Tone Selection**: Domain-specific style palettes (Formal/Scholarly, RFC-style, C-Suite Neutral, etc.)
- **Stylometry Controls**: Hedge density (5-10%), lexical diversity (TTR ≥ 0.40), sentence variability
- **Citation Presentation**: Specific formatting requirements (Bluebook, Chicago, APA, etc.)
- **Structural Formatting**: Markdown compliance, heading hierarchy, list usage

**Auto-Injected Defaults**:
- Moderate hedge density (5-10% of sentences)
- High lexical diversity (no word >2% of tokens)
- Sentence variability (avg 17-22 words, ≥15% <8 words, ≥15% >30 words)
- Rhetorical devices: ≥1 rhetorical question and ≥1 direct-address aside
- No em-dashes; narrative prose preferred over lists unless explicitly requested

### E - Evaluation (Quality Assurance, Verification)

**Purpose**: Implements systematic self-checking and quality validation protocols.

**Standard Protocol (ANCHOR-QR-8)**:
1. **E.1 Reflection Loop**: Self-critique and iterative revision
2. **E.2 Self-Consistency Check**: Multiple reasoning paths for critical outputs
3. **E.3 Chain-of-Verification (CoVe)**: Internal verification questions for complex claims
4. **E.4 Confidence, Sourcing and Accuracy**: Source attribution and `[ExpertJudgment]` tagging
5. **E.5 Style, Safety and Constraint Pass**: Compliance verification
6. **E.6 Overall Fitness and Final Review**: Holistic quality assessment

**Rigor Levels**:
- **Level 1 (Basic)**: Standard ANCHOR-QR-8 evaluation
- **Level 2 (Intermediate)**: Adds 1-2 Advanced Techniques
- **Level 3 (Advanced)**: Comprehensive advanced technique deployment

## Prompt Compliance Evaluation Guidelines

### Essential Compliance Checks

#### Context (C) Component Compliance
- ✓ **Role Definition Present**: Contains "You are a..." statement with 3-5 core role tokens
- ✓ **Persona Clause Quality**: ≤12 words, humanizing detail, no AI/LLM references
- ✓ **Background Completeness**: Provides essential subject matter context
- ✓ **Goal Clarity**: States purpose and intended impact of output
- ✗ **Anti-Patterns**: No parentheses in role, no brand IDs, no AI references

#### Request (R) Component Compliance  
- ✓ **Deliverable Specification**: Clear output type and format requirements
- ✓ **Appropriate Tier Selection**: Word count target matches complexity and use case
- ✓ **Strong Action Verbs**: Uses specific cognitive action words (analyze, synthesize, etc.)
- ✓ **Specificity Level**: Sufficient detail to prevent ambiguous interpretation

#### Examples (E) Component Compliance
- ✓ **Format Demonstration**: If included, examples perfectly match desired output style
- ✓ **Clear Delimiters**: Proper structural separation of examples
- ✓ **Relevance**: Examples directly relate to the requested task
- ✓ **Quality Standards**: Examples meet the quality bar expected for final output

#### Augmentations (A) Component Compliance
- ✓ **Framework Application**: If analytical framework specified, it's correctly identified
- ✓ **Evidence Requirements**: Clear source specification and citation mandates
- ✓ **Live Data Handling**: Appropriate recency filters for volatile information
- ✓ **Advanced Techniques**: Properly integrated reasoning enhancements when needed

#### Tone & Format (T) Component Compliance
- ✓ **Style Consistency**: Tone selection appropriate for audience and domain
- ✓ **Citation Style**: Specific format requirements (Bluebook, Chicago, etc.) clearly stated
- ✓ **Stylometry Requirements**: Meets auto-injected requirements for diversity and variability
- ✓ **Structural Formatting**: Clear heading hierarchy and markdown compliance

#### Evaluation (E) Component Compliance
- ✓ **Standard Protocol**: ANCHOR-QR-8 fully implemented
- ✓ **Appropriate Rigor**: Rigor level matches task complexity and stakes
- ✓ **Prompt-Specific Checks**: Custom validation appropriate to task type
- ✓ **Safety Measures**: PII avoidance, bias mitigation, constraint adherence

### Quality Assessment Metrics

#### Structural Quality (0-10 Scale)
- **10**: All components present, properly structured, comprehensive
- **8-9**: Minor gaps in one component, overall strong structure
- **6-7**: One component significantly incomplete, others adequate
- **4-5**: Multiple components incomplete or poorly structured
- **0-3**: Framework structure not recognizable or severely deficient

#### Content Depth Score (0-10 Scale)
- **10**: Exceptional detail and specificity in all relevant areas
- **8-9**: Strong detail with minor areas lacking depth
- **6-7**: Adequate depth for most components, some shallow areas
- **4-5**: Generally shallow with occasional deeper elements
- **0-3**: Consistently superficial or incomplete content

#### Technical Precision Score (0-10 Scale)
- **10**: Perfect adherence to technical specifications and requirements
- **8-9**: Minor technical inconsistencies, generally precise
- **6-7**: Some technical errors or imprecision, mostly accurate
- **4-5**: Multiple technical issues, questionable accuracy
- **0-3**: Significant technical problems, unreliable specifications

### Compliance Red Flags

#### Critical Failures (Immediate Revision Required)
- AI/LLM references in role definition
- Missing or vague deliverable specification
- Incorrect tier selection for complexity level
- No evidence requirements for factual tasks
- Missing evaluation protocols
- Safety constraint violations

#### Warning Indicators (Review Recommended)
- Generic or overly broad role definitions
- Weak action verbs ("discuss," "talk about")
- Insufficient background context
- Misaligned tone for target audience
- Missing framework specification for analytical tasks
- Inadequate source attribution requirements

### Advanced Compliance Features

#### Error Prevention Patterns
- ✓ **[ExpertJudgment]** tags for unsourced claims
- ✓ **[Confidence:Low]** flags for uncertain assertions
- ✓ **[VerificationIssue]** markers for internal contradictions
- ✓ **[DataUnavailableOrUnverified]** for missing critical information

#### Progressive Evaluation Indicators
- **Minimal (Tiers 1-3)**: Basic consistency and [ExpertJudgment] tagging
- **Standard (Tiers 4-6)**: CoVe, confidence assessment, error forecasting
- **Full (Tiers 7-10)**: Advanced techniques, adversarial testing, numerical confidence

#### Success Criteria Definition
- **Measurable**: Objective, quantifiable success metrics
- **Specific**: Clear requirements rather than vague quality descriptors
- **Aligned**: Success criteria match the stated goal and deliverable
- **Complete**: All critical success factors identified and specified

### Human Review Checklist

#### Factual Accuracy Verification
- [ ] All factual claims supported by specified sources
- [ ] Citations correctly formatted and relevant
- [ ] No fabricated details or hallucinations
- [ ] Appropriate uncertainty flagging

#### Structural Compliance Check
- [ ] All CREATE components properly implemented
- [ ] Tier-appropriate length and complexity
- [ ] Framework correctly applied if specified
- [ ] Style requirements met

#### Quality Assurance Validation
- [ ] Request fully addressed
- [ ] Appropriate depth for intended audience
- [ ] Logical coherence throughout
- [ ] Safety and constraint adherence

This framework provides the foundation for systematic, high-quality prompt engineering that produces reliable, accurate, and fit-for-purpose AI outputs across diverse professional domains.

---

## Journey 1 Implementation Analysis

### Current Alignment Assessment: **65% Aligned**

Based on analysis of the current Journey 1 implementation (`src/ui/journeys/journey1_smart_templates.py`) and CreateAgent (`src/agents/create_agent.py`), the system demonstrates good structural understanding of the CREATE framework but has significant gaps in actual implementation.

### Strong Alignments ✅

#### Framework Component Structure
- **Complete C.R.E.A.T.E. Implementation**: All 6 components properly structured in breakdown generation
- **HyDE Integration**: Three-tier query specificity assessment (low/medium/high) aligns with framework's adaptive enhancement
- **Tier-Based Depth System**: Correctly implements 10-tier system from Nano (≤60 words) to Max-Window Synthese (50,000+ words)
- **File Processing Integration**: Well-integrated content analysis supports context gathering requirements
- **Conceptual Mismatch Detection**: Prevents framework misapplication when users confuse software capabilities

#### Technical Architecture
- **Mock Implementation Strategy**: Graceful fallback ensures system functionality during development
- **Multi-format Support**: Handles text, PDF, CSV, JSON, and DOCX files for comprehensive input processing
- **Content Structure Analysis**: Sophisticated analysis of content type, complexity, and characteristics

### Critical Gaps ❌

#### 1. CreateAgent Underutilization
**Current State**: Placeholder implementation with basic string template generation
```python
def generate_prompt(self, context, preferences=None):
    return f"# Generated C.R.E.A.T.E. Prompt\n\nAgent: {self.agent_id}\nContext: {context}"
```
**Required**: Sophisticated framework knowledge integration with vector search and contextual augmentation

#### 2. ANCHOR-QR Protocol Missing
**Current State**: No implementation of ANCHOR-QR-8 evaluation protocol
**Required**: 6-step evaluation system with diagnostic flags:
- E.1 Reflection Loop with iterative revision
- E.2 Self-Consistency Check with multiple reasoning paths  
- E.3 Chain-of-Verification (CoVe) for complex claims
- E.4 Confidence scoring with `[ExpertJudgment]` tagging
- E.5 Style, Safety and Constraint Pass
- E.6 Overall Fitness and Final Review

#### 3. Knowledge Base Disconnect
**Current State**: Attempts to load CREATE knowledge files but falls back to mock implementations
**Required**: Full RAG integration with vector search and semantic retrieval from knowledge base

#### 4. Framework Library Integration
**Current State**: Limited framework application with basic rule-based selection
**Required**: Systematic framework selection from comprehensive library (SWOT, IRAC, STRIDE, CBA, etc.)

### Component-Specific Analysis

#### Context (C) Component
- ✅ **Good**: Role determination logic based on query analysis
- ❌ **Gap**: Missing persona clause generation (≤12 words, humanizing detail)
- ❌ **Gap**: No filtering of AI/LLM references in role definitions
- ❌ **Gap**: Background context relies on templates rather than domain knowledge

#### Request (R) Component  
- ✅ **Good**: Deliverable specification and format determination
- ❌ **Gap**: Action verb optimization lacks sophistication
- ❌ **Gap**: Tier selection needs more nuanced complexity analysis
- ❌ **Gap**: Missing integration with success criteria definition

#### Examples (E) Component
- ❌ **Critical**: Few-shot examples are generic templates, not framework-driven demonstrations
- ❌ **Gap**: No clear delimiter usage (`### Example ###` patterns)
- ❌ **Gap**: Examples don't demonstrate desired output quality and style
- ❌ **Gap**: No relevance matching to specific task types

#### Augmentations (A) Component
- ❌ **Critical**: Framework selection is rule-based rather than knowledge-driven
- ❌ **Gap**: Missing live data integration patterns with `web.search_query`
- ❌ **Gap**: No advanced reasoning mode integration (Chain-of-Thought, Tree-of-Thought)
- ❌ **Gap**: Evidence specification lacks sophistication

#### Tone & Format (T) Component
- ✅ **Good**: Basic tone determination from query analysis
- ❌ **Gap**: Missing stylometry controls (hedge density 5-10%, lexical diversity TTR ≥ 0.40)
- ❌ **Gap**: No auto-injected defaults from ANCHOR-QR-7
- ❌ **Gap**: Citation presentation lacks specific format requirements

#### Evaluation (E) Component
- ❌ **Critical**: Complete absence of ANCHOR-QR-8 implementation
- ❌ **Critical**: No progressive validation system with diagnostic flags
- ❌ **Gap**: Success criteria are generic rather than measurable and specific
- ❌ **Gap**: Missing rigor level integration (Basic/Intermediate/Advanced)

## Recommended Implementation Roadmap

### Phase 1: Foundation Strengthening (Immediate - High Impact)

#### 1.1 CreateAgent Enhancement
**Priority**: Critical
**Effort**: 3-5 days
**Impact**: Transforms core framework application

**Actions**:
- Replace placeholder `generate_prompt()` with sophisticated CREATE framework logic
- Integrate with knowledge base files for contextual augmentation
- Implement proper role generation with persona clause rules
- Add framework selection algorithms based on query analysis

```python
# Target Implementation Pattern
def generate_prompt(self, context, preferences=None):
    # Load relevant knowledge chunks via RAG
    knowledge_context = self.knowledge_retriever.get_relevant_chunks(context['query'])
    
    # Apply CREATE framework with knowledge integration
    create_structure = self.build_create_components(context, knowledge_context)
    
    # Generate sophisticated prompt with ANCHOR-QR protocols
    return self.render_create_prompt(create_structure, preferences)
```

#### 1.2 ANCHOR-QR-8 Protocol Implementation
**Priority**: Critical  
**Effort**: 4-6 days
**Impact**: Enables quality validation and professional standards

**Actions**:
- Implement 6-step evaluation protocol in Journey 1 output generation
- Add diagnostic flag generation (`[ExpertJudgment]`, `[Confidence:Low]`, `[VerificationIssue]`)
- Integrate evaluation footer with tier suggestions and feedback loops
- Create progressive validation based on task complexity

#### 1.3 Framework Library Integration
**Priority**: High
**Effort**: 2-3 days  
**Impact**: Unlocks sophisticated analytical capabilities

**Actions**:
- Implement systematic framework selection from knowledge base
- Create mapping logic: query type → appropriate frameworks (SWOT, IRAC, STRIDE)
- Add evidence-based reasoning pattern integration
- Include methodology selection based on domain and complexity

### Phase 2: Knowledge Integration (Short-term - Architectural)

#### 2.1 RAG Pipeline Connection
**Priority**: High
**Effort**: 5-7 days
**Impact**: Transforms mock implementations into real knowledge application

**Actions**:
- Replace `_load_create_knowledge_from_files()` with vector search integration
- Implement semantic retrieval for contextual augmentation
- Create knowledge chunk relevance scoring and selection
- Add dynamic knowledge base updates and versioning

#### 2.2 Stylometry Controls Implementation  
**Priority**: Medium
**Effort**: 2-3 days
**Impact**: Enables professional writing standards compliance

**Actions**:
- Integrate ANCHOR-QR-7 auto-injected defaults
- Implement hedge density controls (5-10% of sentences)
- Add lexical diversity requirements (TTR ≥ 0.40)
- Create sentence variability enforcement (avg 17-22 words)

#### 2.3 Advanced Reasoning Integration
**Priority**: Medium
**Effort**: 3-4 days
**Impact**: Enables sophisticated analytical processing

**Actions**:
- Implement Chain-of-Thought and Tree-of-Thought integration
- Add advanced technique selection from ANCHOR-QR-11
- Create rigor level mapping (Basic/Intermediate/Advanced)
- Integrate confidence scoring and uncertainty quantification

### Phase 3: System Optimization (Medium-term - Enhancement)

#### 3.1 Progressive Evaluation System
**Priority**: Medium
**Effort**: 4-5 days
**Impact**: Enables quality assurance and reliability

**Actions**:
- Implement numerical confidence scoring systems
- Add adversarial robustness self-checks
- Create enhanced self-judgment with comparative analysis
- Integrate stepwise natural language self-critique

#### 3.2 User Experience Enhancement
**Priority**: Medium  
**Effort**: 2-3 days
**Impact**: Improves usability and adoption

**Actions**:
- Add real-time framework compliance indicators
- Implement interactive component adjustment
- Create quality preview with compliance scoring
- Add export functionality for various formats

#### 3.3 Performance Optimization
**Priority**: Low
**Effort**: 3-4 days
**Impact**: Enables scalability and responsiveness

**Actions**:
- Implement caching for knowledge retrieval
- Add parallel processing for component generation
- Optimize vector search performance
- Create intelligent prompt preprocessing

### Implementation Success Metrics

#### Quality Metrics
- **Framework Compliance Score**: Target >90% (current ~65%)
- **ANCHOR-QR Protocol Coverage**: Target 100% (current 0%)
- **Knowledge Integration Depth**: Target >80% knowledge base utilization
- **User Satisfaction**: Target >4.5/5 for prompt quality

#### Technical Metrics  
- **Response Time**: <3 seconds for standard prompts
- **Knowledge Retrieval Accuracy**: >90% relevance scoring
- **System Reliability**: >99.5% uptime for framework generation
- **Component Coverage**: 100% CREATE component implementation

#### Business Impact Metrics
- **Prompt Effectiveness**: Measured via user feedback and outcome tracking
- **Framework Adoption**: Usage patterns and user retention
- **Quality Consistency**: Variance in prompt quality across different query types
- **Professional Standards Compliance**: Adherence to established prompt engineering practices

### Critical Dependencies

#### Technical Dependencies
- **Qdrant Integration**: Vector database connectivity for knowledge retrieval
- **Zen MCP Server**: Agent orchestration and communication protocols  
- **OpenRouter API**: Model integration for enhanced generation
- **Knowledge Base Completeness**: Full ingestion of CREATE framework documentation

#### Organizational Dependencies
- **Development Resource Allocation**: Dedicated engineering time for implementation
- **Quality Assurance**: Testing framework for prompt quality validation
- **User Feedback Integration**: Mechanisms for continuous improvement
- **Documentation Updates**: Maintenance of implementation guides and standards

This roadmap transforms Journey 1 from a structural placeholder into a sophisticated CREATE framework implementation that delivers professional-grade prompt engineering capabilities.