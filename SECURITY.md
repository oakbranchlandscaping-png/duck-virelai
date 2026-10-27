# Security policy

This repository contains research code that can call model servers, Kaggle, and ARC environments. No credential is
required to inspect or test the offline semantic-library code.

- Never commit API keys, Kaggle credentials, model tokens, or private run URLs.
- Treat pickle files and historical run artifacts as untrusted input; do not load them from an untrusted fork.
- Use environment variables or platform secret stores for live credentials.
- Report a suspected credential exposure or code-execution vulnerability through GitHub's private vulnerability
  reporting feature rather than a public issue.

There is no promise of production security support. Reports that protect users of the public code will be reviewed as
time permits.
