# Fix Document Links

Analyze and fix broken internal links in: $ARGUMENTS

## Analysis Required

1. **Identify all internal links** in the specified file(s):
   - Relative links: `[text](./path/file.md)`
   - Absolute repo links: `[text](/docs/path/file.md)`
   - Parent directory links: `[text](../file.md)`
   - Anchor links: `[text](#heading-name)`

2. **Validate each link target**:
   - Check if target file exists
   - Verify anchor links point to valid headings
   - Identify broken or outdated references

3. **Suggest fixes for broken links**:
   - Use fuzzy matching to find similar filenames
   - Check for moved or renamed files
   - Provide correct relative paths

## Common Link Issues in PromptCraft-Hybrid

Based on project structure, watch for these common broken link patterns:

- `./PROJECT_HUB.md` → should be `./project_hub.md`
- `./CONTRIBUTING.md` → should be `../../CONTRIBUTING.md` or `../PC_Contributing.md`
- `./docs/PC_ADR.md` → should be `./ADR.md` (from planning directory)
- `./issues` → should be `./pc_milestones_issues.md`
- Links to moved planning documents in `/docs/planning/`

## Required Output

Provide fixes in this format:

```markdown
# Link Validation Report: [filename]

## ✅ Valid Links
- [Link text](./valid-path.md) ✓

## ❌ Broken Links Found

### 1. [Link Text](./broken-path.md)
- **Issue**: Target file not found
- **Suggested Fix**: `[Link Text](./correct-path.md)`
- **Reason**: File was moved/renamed

### 2. [Another Link](#invalid-anchor)
- **Issue**: Anchor target does not exist
- **Suggested Fix**: `[Another Link](#valid-heading-name)`
- **Reason**: Heading was changed

## 🔧 Corrected File Content

[Provide the complete corrected file with all links fixed]

## Summary
- **Total Links**: [number]
- **Valid Links**: [number]
- **Broken Links**: [number]
- **Fixed Links**: [number]
```

## Instructions

1. **Read the specified file(s)** and extract all internal links
2. **Validate each link** against the actual repository structure
3. **Identify broken links** and determine the cause
4. **Suggest specific fixes** with correct paths
5. **Provide the corrected file content** with all links fixed
6. **Ensure fixes maintain context** and don't break the document flow

Focus on providing actionable, specific fixes that can be immediately applied.
