## What and why

<!-- What does this change, and what problem does it solve? Link the issue if there is one. -->

## Checklist

- [ ] `python -m pytest -q tests` passes
- [ ] Tested a real fleet: `pfe spawn 2 --validate` (if it touches the spawner or node image)
- [ ] New input that reaches the compose file goes through `validate()` and has a test
- [ ] README / `docker/DOCKERHUB-*.md` updated if behaviour or settings changed
- [ ] Line added under `## [Unreleased]` in `CHANGELOG.md`
