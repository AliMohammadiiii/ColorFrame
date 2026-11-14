# Security

## Credentials

ColorFrame uses Modal for benchmark execution. Modal credentials are **never** stored in this repository.

- Authenticate with `modal token set` (writes to `~/.modal.toml`, outside the repo) or export
  `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` in your shell environment.
- Never paste token values into source files, notebooks, documentation, commit messages,
  benchmark outputs, issue trackers, or chat transcripts.
- `.gitignore` excludes `.env*`, `.modal.toml`, `*.pem` and `private/`.
- Benchmark metadata records the Modal *workspace profile name* only, never token values.

## Incident log

| Date | Event | Action |
|---|---|---|
| before 2026-11-14 | A Modal credential was exposed in an earlier conversation. | Treated as compromised; not used. Revocation is the owner's responsibility. |
| 2026-11-14 | A newly issued Modal token was pasted into an AI-assistant chat while configuring the `cytognosis` profile. | Values were not copied into any file in this repo. **Owner action required:** rotate this token in the Modal dashboard after the benchmark session. |

## Checking authentication safely

```bash
modal profile current      # prints the profile name only
modal app list             # succeeds only when authenticated
```

## Pre-commit secret check

Before every merge to `main` we run:

```bash
git grep -nIE '(ak-[A-Za-z0-9]{10,}|as-[A-Za-z0-9]{10,}|MODAL_TOKEN_SECRET=)' -- . ':!SECURITY.md' || echo "no secrets found"
```
