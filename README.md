# VERIFY Research System
VERIFY-powered Academic Research Platform: Fact-verified AI research with PRISMA Assistant for systematic literature reviews

## Installation

Install the entire system in development mode:

```bash
pip install -e .
```

### PRISMA Assistant CLI

After installation, use the PRISMA Assistant CLI:

```bash
prisma-assistant --help
prisma-assistant init --topic "diabetes treatment" --domain "medical"
prisma-assistant screen --input papers.csv --output results.json
```
