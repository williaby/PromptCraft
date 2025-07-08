# C.R.E.A.T.E. Framework Templates

This directory contains template files for the C.R.E.A.T.E. framework prompt enhancement system.

## Template Structure

Each template is a YAML file with the following structure:

```yaml
metadata:
  name: "Template Name"
  description: "Template description"
  type: "business|technical|legal|academic|creative"
  version: "1.0"
  author: "PromptCraft"
  created_date: "2025-01-01"
  modified_date: "2025-01-01"
  tags: ["tag1", "tag2"]

variables:
  variable_name:
    type: "string|number|boolean"
    description: "Variable description"
    required: true|false

structure:
  sections:
    - name: "section_name"
      description: "Section description"
      template: "Template content with {variable_name}"

examples:
  - name: "Example name"
    variables:
      variable_name: "Example value"
```

## Available Templates

### Business Templates
- `business_email.yaml` - Professional business email template

### Technical Templates
- `technical_documentation.yaml` - Technical documentation template

## Usage

Templates are loaded and managed by the `TemplateManager` class in `src/core/template_system_core.py`.

```python
from src.core.template_system_core import TemplateManager, TemplateProcessor

# Initialize template system
manager = TemplateManager("knowledge/create_agent/templates")
processor = TemplateProcessor(manager)

# Process a template
variables = {"title": "My Document", "content": "Document content"}
result = processor.process_template("technical_documentation", variables)
```

## Contributing

When adding new templates:

1. Follow the YAML structure outlined above
2. Include comprehensive metadata
3. Provide clear variable descriptions
4. Include at least one example
5. Test the template with the validation system