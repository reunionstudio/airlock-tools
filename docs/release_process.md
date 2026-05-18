# Release Process

This repository should use GitHub Releases with SemVer-style tags.

## Version Policy

- Use tags in the form `vMAJOR.MINOR.PATCH`.
- Keep `pyproject.toml`, `src/airlock_mcp/__init__.py`, and
  `CHANGELOG.md` aligned.
- During `0.x`, minor releases may add or change supported tool behavior. Patch
  releases should be bugfixes, docs corrections, and compatibility fixes.
- If a release requires a new Airlock stored procedure signature or return
  contract, name the minimum Airlock API version or installed documentation hash
  in the release notes.

## Before Tagging

1. Confirm the working tree contains only intended changes.
2. Run:
   ```bash
   uv run --extra dev ruff check .
   uv run --extra dev pytest
   git diff --check
   uv build
   ```
3. Update `CHANGELOG.md`.
4. Update versions in `pyproject.toml` and `src/airlock_mcp/__init__.py` if this
   is not the initial `0.1.0` release.
5. Confirm the public repo has the intended license, repository URL, package
   name, and release target.
6. Commit the release.
7. Create an annotated tag:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   ```
8. Push the commit and tag, then create a GitHub Release from the tag.

## Distribution

For `v0.1.0`, publish in this order:

1. GitHub Release from the tag.
2. Python package named `airlock-tools`, when package publishing is ready.
3. Cortex Code skill instructions pointing to the released Git tag.
4. Optional Snowflake stage copy of `.cortex/skills` for customers that want
   Snowflake-role-controlled skill distribution.

## Release Notes

Release notes should say:

- where to install the MCP server package or Git release
- how to add the Cortex Code skill
- what changed for MCP users
- what changed for Cortex Code skills
- whether installed Airlock procedure contracts changed
- whether any safety defaults changed
- which tests were run
