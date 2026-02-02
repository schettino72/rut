# LLM Integration

This folder contains resources for LLM tools to understand and work with rut.

## Contents

### llms.txt / llms-full.txt

Standard discovery files for LLMs. See [llmstxt.org](https://llmstxt.org/) for the specification.

- `llms.txt` - Concise overview (quick reference)
- `llms-full.txt` - Complete documentation (detailed reference)

### claude-plugin/

A [Claude Code plugin](https://code.claude.com/docs/en/plugins) that teaches Claude to use rut for running tests.

**Installation:**

```
/plugin marketplace add schettino72/rut
/plugin install rut-testing@rut
```

**Contents:**
- `skills/rut-testing/SKILL.md` - Workflow instructions (always loaded)
- `skills/rut-testing/REFERENCE.md` - Detailed configuration and examples (loaded on-demand)
