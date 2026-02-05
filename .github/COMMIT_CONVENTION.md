# Commit Message Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automatic semantic versioning.

## Version Bumping Rules

The semantic versioning workflow automatically determines the version bump based on commit messages:

| Commit Pattern | Version Bump | Example |
|---------------|--------------|---------|
| Any commit | **PATCH** (0.0.+1) | `fix: resolve parsing error`<br>`docs: update readme`<br>`chore: cleanup` |
| `feat:` or `feat(scope):` | **MINOR** (0.+1.0) | `feat: add SVG output format`<br>`feat(cli): add --open flag` |
| `BREAKING CHANGE:` in body<br>or `!` after type | **MAJOR** (+1.0.0) | `feat!: remove Flask web UI`<br>`refactor!: rewrite parser`<br>Message with `BREAKING CHANGE:` in body |

## Commit Message Format

```
<type>[optional scope][optional !]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: New feature (triggers **MINOR** bump)
- **fix**: Bug fix (triggers **PATCH** bump)
- **docs**: Documentation changes (triggers **PATCH** bump)
- **style**: Code style changes (formatting, etc.) (triggers **PATCH** bump)
- **refactor**: Code refactoring (triggers **PATCH** bump)
- **test**: Adding or updating tests (triggers **PATCH** bump)
- **chore**: Maintenance tasks (triggers **PATCH** bump)
- **perf**: Performance improvements (triggers **PATCH** bump)
- **ci**: CI/CD changes (triggers **PATCH** bump)
- **build**: Build system changes (triggers **PATCH** bump)
- **revert**: Revert previous commit (triggers **PATCH** bump)

### Examples

#### Patch Bump (0.3.0 → 0.3.1)
```bash
git commit -m "fix: handle missing stage attribute in jobs"
git commit -m "docs: update installation instructions"
git commit -m "chore: update dependencies"
git commit -m "style: format code with black"
```

#### Minor Bump (0.3.0 → 0.4.0)
```bash
git commit -m "feat: add support for remote includes"
git commit -m "feat(cli): add --verbose flag for debugging"
git commit -m "feat(parser): support YAML anchors and aliases"
```

#### Major Bump (0.3.0 → 1.0.0)
```bash
# Using ! after type
git commit -m "feat!: change CLI arguments structure"
git commit -m "refactor!: remove deprecated API methods"

# Using BREAKING CHANGE in body
git commit -m "feat: rewrite configuration parser

BREAKING CHANGE: The parser now requires Python 3.9+ and 
the old JSON format is no longer supported."
```

#### With Scope
```bash
git commit -m "feat(api): add GraphQL endpoint"
git commit -m "fix(parser): resolve circular include detection"
git commit -m "docs(readme): add usage examples"
```

## Automation

The `.github/workflows/version.yml` workflow automatically:

1. ✅ Analyzes commit messages since the last version tag
2. ✅ Determines the appropriate version bump
3. ✅ Updates `pyproject.toml` with the new version
4. ✅ Creates a Git tag (e.g., `v0.4.0`)
5. ✅ Pushes the changes and tag to the repository
6. ✅ Creates a GitHub Release

## Skip CI

To prevent the version commit from triggering another workflow run, the bot includes `[skip ci]` in its commit message:

```
chore: bump version to 0.4.0 [skip ci]
```

## Current Version

Check the current version:
```bash
# In pyproject.toml
grep version pyproject.toml

# Latest Git tag
git describe --tags --abbrev=0

# Using GitHub CLI
gh release list
```

## Best Practices

1. **Write clear, descriptive commit messages** - They become your changelog
2. **Use conventional format** - Enables automatic versioning
3. **One logical change per commit** - Makes version bumps predictable
4. **Use breaking change markers sparingly** - Reserve for real API changes
5. **Add scope when helpful** - Makes it easier to find related changes

## References

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [paulhatch/semantic-version Action](https://github.com/paulhatch/semantic-version)
