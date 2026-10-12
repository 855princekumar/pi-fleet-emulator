# Contributing

Thanks for helping improve Pi Fleet Emulator. Bug reports, ideas and pull requests are all welcome.

## Ground rules

- Be kind: this project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
- **Security problems:** please don't open a public issue. Report them privately as described in [SECURITY.md](SECURITY.md).
- Bigger changes: open an issue first so we can agree on the approach.

## Set up

```bash
git clone https://github.com/855princekumar/pi-fleet-emulator.git
cd pi-fleet-emulator
python -m venv venv && . venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Test before you push

```bash
python -m pytest -q tests                        # unit tests, no Docker needed
docker compose up -d --build                     # full stack from source
docker exec pi-fleet-spawner pfe spawn 2 --validate
docker exec pi-fleet-spawner pfe reset --yes && docker compose down -v
```

Every pull request runs the same checks in [CI](.github/workflows/ci.yml): unit tests, a real 2-node fleet (validation, scaling, persistence, attack checks), image security scans, and a release dry-run.

## Conventions

- **Shell scripts** under `node-base/` must keep LF line endings (`.gitattributes` enforces it); CRLF breaks them inside the container.
- **Anything that reaches the generated compose file** must go through `validate()` in `spawner/app.py`, with a test in `tests/`.
- **GitHub Actions** are pinned to full commit SHAs with the version in a comment.
- **Docs:** update the README (and `docker/DOCKERHUB-*.md` if the Docker Hub page is affected) in the same pull request.
- Add a line under a new `## [Unreleased]` heading in [CHANGELOG.md](CHANGELOG.md).

## Good first areas

More simulated Pi commands (`vcgencmd`, `raspi-config`), GPIO stubs, per-node resource limits, and more scenarios for [TEST-PLAYGROUND.md](TEST-PLAYGROUND.md).

## License

By contributing you agree that your contribution is dual-licensed under [MIT](LICENSE-MIT) and [Apache 2.0](LICENSE-APACHE), like the rest of the project.
