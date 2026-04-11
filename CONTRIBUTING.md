# Contributing

Thanks for taking the time to contribute.

## Before you start

1. Check the [issues](../../issues) to see if someone is already working on the same thing.
2. For anything non-trivial, open an issue first so we can agree on the approach before you write code.
3. For small fixes (typos, docs, obvious bugs), feel free to open a pull request directly.

## Development workflow

1. Fork the repository and clone your fork.
2. Create a feature branch from the default branch using one of these prefixes: `feature/`, `fix/`, `docs/`, `refactor/`, `chore/`, `test/`, `hotfix/`, `release/`.
3. Make your changes in small, logical commits.
4. Write or update tests where appropriate.
5. Run the project's test suite and linter locally.
6. Push to your fork and open a pull request against the default branch.

## Pull requests

- Keep pull requests focused. One logical change per PR.
- Link any related issues in the description (for example, `Closes #123`).
- Fill in the PR template checklist.
- Expect review feedback and iterate.
- Merges are done via squash or rebase to keep history linear.
- The default branch is protected. You cannot push directly, you must open a pull request.

## Commit messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) style:

```
<type>(<optional scope>): <short summary>
```

Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`.

Example: `fix(auth): handle expired refresh tokens on reload`

## Code style

Follow the conventions already used in the codebase. Match the surrounding indentation, naming and layout. If the project has a linter or formatter configured, run it before committing.

## Reporting bugs

Please use the bug report issue template. Include:

- What you expected to happen.
- What actually happened.
- Steps to reproduce.
- Your environment (OS, language version, relevant package versions).

## Proposing features

Please use the feature request issue template. Explain the problem you are trying to solve before the solution you have in mind.

## Code of conduct

This project follows the [Contributor Covenant Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

## Security issues

If you think you have found a security vulnerability, please do **not** open a public issue. Use GitHub's private vulnerability reporting feature under the Security tab of this repository.

## License

By submitting a contribution, you agree that your contribution will be licensed under the same license as the project.
