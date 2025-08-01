# Validate Knowledge Chunk

Ensure H3 sections are truly atomic, self-contained, and optimized for RAG retrieval: $ARGUMENTS

## Expected Arguments

- **File Path**: Path to knowledge file to validate (e.g., `knowledge/security_agent/oauth2-guide.md`)

## Analysis Required

1. **Heading Structure Analysis**: Verify H1-H3 hierarchy compliance
2. **Atomic Chunk Validation**: Ensure each H3 section is self-contained
3. **Context Dependency Check**: Identify forward/backward references
4. **RAG Optimization**: Validate content for vector database retrieval
5. **Content Completeness**: Ensure chunks include sufficient context
6. **Cross-Reference Validation**: Check internal and external links

## Atomic Knowledge Chunk Requirements

### Self-Containment Rules

Each H3 section must be **completely understandable in isolation**:

- ✅ **Complete Context**: All necessary background information included
- ✅ **No Forward References**: Doesn't rely on content from later sections
- ✅ **No Backward Dependencies**: Doesn't assume reader has read previous sections
- ✅ **Standalone Value**: Provides actionable information by itself
- ✅ **Clear Scope**: Clearly defined topic boundary

### Content Completeness Standards

Every H3 chunk should include:

- **Topic Introduction**: What this section covers
- **Context/Background**: Why this information matters
- **Core Content**: The actual knowledge or instructions
- **Examples/Implementation**: Practical application when relevant
- **Key Takeaways**: Critical points to remember

### RAG Optimization Criteria

Content must be optimized for vector search retrieval:

- **Descriptive Headers**: H3 titles clearly indicate content
- **Keyword Rich**: Includes relevant technical terms naturally
- **Semantic Clarity**: Concepts explained in clear, searchable language
- **Embedding Friendly**: Content length appropriate for vector encoding
- **Query Alignment**: Matches likely user query patterns

## Validation Checks

### 1. Heading Structure Validation

```markdown
# Document Title                    ✅ Exactly one H1
## Major Section                   ✅ H2 for grouping topics
### Atomic Knowledge Chunk         ✅ H3 for retrievable units
#### Sub-detail                    ❌ PROHIBITED - breaks chunking
```

### 2. Self-Containment Analysis

**Forward Reference Detection**:

- ❌ "As we'll see in the next section..."
- ❌ "The implementation details follow..."
- ❌ "This will be covered later..."

**Backward Dependency Detection**:

- ❌ "As mentioned earlier..."
- ❌ "Using the previous configuration..."
- ❌ "Building on our earlier example..."

**Assumption Detection**:

- ❌ Assumes reader knows previous context
- ❌ References variables/concepts not defined in chunk
- ❌ Continues explanations from other sections

### 3. Content Completeness Check

**Required Elements**:

- [ ] **Context Setting**: Why this topic matters
- [ ] **Complete Explanation**: Full concept coverage
- [ ] **Practical Application**: How to use this knowledge
- [ ] **Examples**: Concrete implementations where relevant
- [ ] **Error Handling**: Common issues and solutions

**Missing Context Indicators**:

- Undefined acronyms or technical terms
- Code snippets without setup context
- Procedures without prerequisites
- Examples without explanation

### 4. RAG Retrieval Optimization

**Optimal Chunk Characteristics**:

- **Length**: 200-800 words (optimal for embeddings)
- **Structure**: Clear topic progression
- **Terminology**: Consistent use of keywords
- **Completeness**: Answers likely user questions
- **Actionability**: Provides usable information

**Query Match Assessment**:

- Would users naturally search for this content?
- Does the H3 title match expected search terms?
- Are key concepts mentioned in searchable language?
- Does content answer complete user questions?

## Common Anti-Patterns

### 1. Context Dependencies

```markdown
❌ BAD - References other sections:
### JWT Token Validation
Using the secret key from the previous section, validate tokens...

✅ GOOD - Self-contained:
### JWT Token Validation
JWT tokens require validation using a secret key to ensure authenticity.
First, obtain your secret key from your application configuration...
```

### 2. Incomplete Context

```markdown
❌ BAD - Missing setup:
### Running Database Migrations
Execute the following command:
```bash
python manage.py migrate
```

✅ GOOD - Complete context:

### Running Database Migrations

Database migrations update your database schema to match model changes.
Before running migrations, ensure you have:

- Virtual environment activated
- Database connection configured
- Django settings properly configured

Execute migrations with:

```bash
python manage.py migrate
```

```

### 3. Overly Granular Sections
```markdown
❌ BAD - Too granular:
### Step 1: Import Required Libraries
### Step 2: Configure Settings
### Step 3: Initialize Client

✅ GOOD - Appropriate scope:
### OAuth2 Client Setup
Setting up an OAuth2 client requires importing libraries, configuring
settings, and initializing the client connection...
```

## Required Output Format

### Validation Report Structure

```markdown
# Knowledge Chunk Validation Report

## File: {file_path}

### 📊 CHUNK ANALYSIS SUMMARY
- **Total H3 Sections**: 8
- **Atomic Chunks**: 6 ✅
- **Non-Atomic Chunks**: 2 ❌
- **RAG Optimized**: 7 ✅
- **Context Complete**: 5 ✅

### ❌ NON-ATOMIC CHUNKS

#### Section: "JWT Token Validation" (Line 45)
**Issues:**
- Forward reference: "using the secret key from the previous section"
- Missing context: Secret key generation not explained
- Incomplete: No error handling for invalid tokens

**Recommendation**: Include complete JWT validation workflow with key generation and error handling.

#### Section: "Error Handling" (Line 78)
**Issues:**
- Backward dependency: References "configuration from Step 2"
- Incomplete context: Doesn't define which errors to handle
- Missing examples: No concrete error scenarios

**Recommendation**: Make self-contained with complete error taxonomy and handling examples.

### ⚠️ RAG OPTIMIZATION ISSUES

#### Section: "Setup" (Line 12)
**Issues:**
- Generic title: Won't match specific user queries
- Too broad: Covers multiple distinct topics
- Missing keywords: Lacks searchable technical terms

**Recommendation**: Split into specific sections like "OAuth2 Configuration Setup" and "Environment Variables Setup".

### ✅ EXCELLENT ATOMIC CHUNKS

#### Section: "Client Credentials Flow Implementation"
- Completely self-contained with full context
- Includes prerequisites, implementation, and validation
- Optimal length for RAG retrieval (456 words)
- Rich in searchable keywords

### 🔧 SPECIFIC FIXES NEEDED

1. **JWT Token Validation Section**:
   ```markdown
   ### JWT Token Validation and Secret Key Management

   JWT (JSON Web Token) validation ensures token authenticity using cryptographic signatures.
   This process requires a secret key for HMAC signing or public/private keys for RSA/ECDSA.

   #### Secret Key Generation
   Generate a secure secret key for HMAC algorithms:
   [Complete implementation...]
   ```

2. **Error Handling Section**:

   ```markdown
   ### OAuth2 Error Handling and Recovery

   OAuth2 implementations must handle various error scenarios including expired tokens,
   invalid grants, and network failures. This section covers comprehensive error handling patterns.

   #### Common Error Types
   [Complete error taxonomy...]
   ```

### 📈 CHUNK QUALITY SCORES

- **Atomic Compliance**: 75% (6/8 chunks)
- **RAG Optimization**: 87% (7/8 chunks)
- **Context Completeness**: 62% (5/8 chunks)
- **Overall Quality**: 75%

### 💡 RECOMMENDATIONS

1. Combine related granular sections into comprehensive chunks
2. Add missing context to dependent sections
3. Include concrete examples in abstract sections
4. Use more specific, searchable section titles
5. Ensure each chunk answers complete user questions

```

## Validation Scope

### Individual File Analysis
- Deep analysis of all H3 sections
- Context dependency mapping
- RAG optimization assessment
- Specific improvement recommendations

### Batch Directory Analysis
- Consistency across agent knowledge base
- Common pattern identification
- Bulk optimization recommendations
- Agent-specific quality metrics

## Important Notes

- Validation enforces docs/planning/knowledge_style_guide.md standards
- Focus on RAG pipeline optimization for vector search
- Each H3 section should be valuable in isolation
- Balance between atomic chunks and complete context
- Consider user query patterns when optimizing content
- Provide actionable recommendations for improvement
- Support both individual file and batch analysis modes
