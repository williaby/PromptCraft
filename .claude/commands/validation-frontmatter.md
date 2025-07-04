# Validate Front Matter

Validate and fix YAML front matter in: $ARGUMENTS

## Validation Rules

### Knowledge Files (`/knowledge/` directory)
Required YAML front matter structure:
```yaml
---
title: [String - must match H1 heading exactly]
version: [X.Y or X.Y.Z semantic version]
status: [draft|in-review|published]
agent_id: [snake_case - MUST match folder name exactly]
tags: [Array of lowercase strings, use underscores for spaces]
purpose: [Single sentence ending with period]
---
```

### Planning Documents (`/docs/planning/` directory)
Required YAML front matter structure:
```yaml
---
title: [String - must match H1 heading exactly]
version: [X.Y or X.Y.Z semantic version]
status: [draft|in-review|published]
component: [Strategy|Development-Tools|Context|Request|Examples|Augmentations|Tone-Format|Evaluation]
tags: [Array of lowercase strings, use underscores for spaces]
source: [String - reference to originating document]
purpose: [Single sentence ending with period]
---
```

## Validation Checks

1. **Presence**: YAML front matter exists and is properly formatted
2. **Required Fields**: All mandatory fields are present
3. **Title Consistency**: YAML title matches H1 heading exactly
4. **Agent ID Consistency** (knowledge files): agent_id matches folder name
5. **Status Workflow**: Status follows draft → in-review → published
6. **Tag Format**: Tags are lowercase with underscores (not spaces or camelCase)
7. **Purpose Format**: Single sentence ending with period
8. **Version Format**: Follows semantic versioning (X.Y or X.Y.Z)

## Analysis Required

1. **Extract current YAML front matter** from the file
2. **Identify file type** (knowledge vs planning vs general)
3. **Check each required field** against validation rules
4. **Compare title with H1 heading** for exact match
5. **Validate agent_id consistency** for knowledge files
6. **Check tag formatting** (lowercase, underscores)

## Required Output

```markdown
# Front Matter Validation Report: [filename]

## Current Front Matter
```yaml
[Show current YAML front matter]
```

## ✅ Valid Fields
- [List fields that pass validation]

## ❌ Issues Found
- **Missing Field**: [field_name] is required but missing
- **Title Mismatch**: YAML title "[yaml_title]" does not match H1 "[h1_title]"
- **Agent ID Mismatch**: YAML agent_id "[yaml_id]" does not match folder "[folder_name]"
- **Invalid Tag Format**: "[tag]" should be "[corrected_tag]" (lowercase with underscores)
- **Invalid Purpose**: Must be single sentence ending with period

## 🔧 Corrected Front Matter
```yaml
---
title: [Corrected title]
version: [Corrected version]
status: [Corrected status]
agent_id: [Corrected agent_id] # for knowledge files
component: [Corrected component] # for planning docs
tags: ['corrected', 'tag_format']
source: "[Corrected source]" # for planning docs
purpose: [Corrected single sentence ending with period]
---
```

## 📝 Additional Recommendations
- [Any suggestions for improving metadata quality]

## Summary
- **File Type**: [knowledge|planning|general]
- **Fields Checked**: [number]
- **Valid Fields**: [number]
- **Issues Found**: [number]
- **Status**: [PASS|FAIL]
```

## Instructions

1. **Read the specified file** and extract YAML front matter
2. **Determine file type** based on directory location
3. **Apply appropriate validation rules** for the file type
4. **Check each field** systematically against requirements
5. **Provide corrected front matter** with all issues fixed
6. **Ensure corrections maintain semantic meaning** while fixing format issues

Be precise about field requirements and provide exact corrections.
