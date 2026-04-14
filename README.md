# envguard

> CLI tool that validates and diffs `.env` files across environments to catch missing or mismatched variables before deployment.

---

## Installation

```bash
pip install envguard
```

Or with pipx for isolated CLI usage:

```bash
pipx install envguard
```

---

## Usage

Compare a local `.env` file against a production template or another environment file:

```bash
# Check for missing variables against a reference file
envguard check --ref .env.production --target .env.local

# Diff two environment files side by side
envguard diff .env.staging .env.production

# Validate all required keys are present and non-empty
envguard validate --ref .env.example --target .env
```

**Example output:**

```
✔  DB_HOST         present in both
✔  API_KEY         present in both
✗  REDIS_URL       missing in .env.local
⚠  LOG_LEVEL       value mismatch (staging: "debug" | production: "info")

2 issues found. Deployment may fail.
```

### Options

| Flag | Description |
|------|-------------|
| `--ref` | Reference `.env` file to validate against |
| `--target` | Target `.env` file to check |
| `--strict` | Exit with non-zero code if any issues are found |
| `--json` | Output results as JSON (useful for CI pipelines) |

---

## CI Integration

```bash
# Fail the pipeline if variables are missing
envguard validate --ref .env.example --target .env --strict
```

---

## License

MIT © [envguard contributors](https://github.com/yourname/envguard)