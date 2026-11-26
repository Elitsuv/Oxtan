## Summary

<!-- Explain what changed and why. Link the tracked issue below. -->
Closes #

## Category & Domain

**Type (`ox:`):**
- [ ] `ox: bug`
- [ ] `ox: feat`
- [ ] `ox: security`
- [ ] `ox: perf`
- [ ] `ox: refactor`
- [ ] `ox: docs`
- [ ] `ox: test`
- [ ] `ox: chore`

**Domain:**
- [ ] `ox: cli`
- [ ] `ox: mysql`
- [ ] `ox: profiles`
- [ ] `ox: output`
- [ ] `ox: ci`

## Verification

- [ ] `ruff check src/ tests/` and `ruff format --check src/ tests/` pass
- [ ] `mypy src/` passes
- [ ] `bandit -r src/` passes
- [ ] `pytest tests/unit tests/cli --cov=oxtan --cov-fail-under=90` passes
- [ ] Added/updated unit tests covering the changes (no secrets or credentials included)
