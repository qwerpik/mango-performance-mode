# Contributing to mango-performance-mode

Thank you for your interest in improving `mango-performance-mode`! Contributions of all kinds — bug reports, fixes, documentation, and desktop themes — are welcome.

## Quick Contribution Workflow (3 Steps)

1. **Fork and Branch**
   - Fork the repository on GitHub.
   - Create a feature branch: `git checkout -b feature/my-enhancement`.

2. **Develop and Test**
   - Make your changes.
   - Run the full test and lint suite locally before committing:
     ```bash
     make check
     ```
   - All tests, `ruff` checks, and `mypy` must pass.

3. **Open a Pull Request**
   - Push your branch to your fork: `git push origin feature/my-enhancement`.
   - Submit a Pull Request against `main` with a clear description of what changed and why.

## Guidelines

- **Zero Runtime Dependencies**: the controller and privileged helper use only the Python standard library. Do not introduce mandatory third-party pip dependencies.
- **Atomic & Concurrency-Safe**: state persistence must keep POSIX advisory file locks (`fcntl.flock`) and atomic file replacement (`os.replace`).
- **Least Privilege**: the `libexec/performance-mode-apply` helper stays fixed-purpose (eco/balanced/max only) with rollback on failure. Do not widen the sudoers rule.
- **Portability**: no hardcoded `/home/...` paths or usernames. Use `PREFIX`, `XDG_*`, and `~`. GPU detection must degrade gracefully (see `MANGO_GPU_DEVICE`).
- **Keep Documentation Synchronized**: if adding flags or config options, update `README.md` and the relevant file in `docs/`.
