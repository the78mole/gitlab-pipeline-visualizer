# PyPI Publication Setup

This document describes how to configure automatic PyPI publication for this project.

## Overview

The project uses GitHub Actions to automatically publish new versions to PyPI whenever a release is created. The workflow (`.github/workflows/publish.yml`) is triggered when:

1. A new GitHub Release is published (automatic via `version.yml` workflow)
2. Manually via workflow_dispatch (for testing)

## Setup Instructions

### 1. Create PyPI API Token

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to "API tokens" section
3. Click "Add API token"
4. Enter token name: `glab-pipeviz-github-actions`
5. Scope: Select "Project: glab-pipeviz" (or "Entire account" for first publish)
6. Click "Add token"
7. **Copy the token immediately** (starts with `pypi-...`)

### 2. Add Token to GitHub Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PYPI_TOKEN`
4. Value: Paste the PyPI token from step 1
5. Click "Add secret"

### 3. Configure PyPI Environment (Optional but Recommended)

For additional security, create a deployment environment:

1. Go to repository Settings → Environments
2. Click "New environment"
3. Name: `pypi`
4. Add protection rules (optional):
   - Required reviewers
   - Wait timer
   - Deployment branches (only main)
5. Save

The workflow is already configured to use this environment.

## First Publication

For the **first publication** to PyPI, you need to:

### Option A: Manual Registration (Recommended)

1. Build the package locally:
   ```bash
   uv build
   ```

2. Register on PyPI with broad token scope:
   - Create an API token with "Entire account" scope
   - Add it to GitHub Secrets as `PYPI_TOKEN`

3. Let the workflow publish automatically on next release

### Option B: Manual First Upload

1. Build locally:
   ```bash
   uv build
   ```

2. Upload manually:
   ```bash
   uv publish
   # Or with explicit token:
   # uv publish --token pypi-your-token-here
   ```

3. After first upload, create a project-scoped token and update the GitHub Secret

## Trusted Publishers (Alternative)

PyPI supports "Trusted Publishers" which doesn't require storing tokens. To set this up:

1. Go to [PyPI Project Settings](https://pypi.org/manage/project/glab-pipeviz/settings/publishing/)
2. Add a new publisher:
   - **Owner**: `twidi` (your GitHub username/org)
   - **Repository name**: `gitlab-pipeline-visualizer`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

3. Modify `.github/workflows/publish.yml` to use OIDC:
   ```yaml
   permissions:
     id-token: write  # Required for trusted publishing
     contents: read
   
   # Replace uv publish step with:
   - name: Publish to PyPI
     run: uv publish --trusted-publishing
   ```

## Testing the Workflow

### Test with TestPyPI

Before publishing to the real PyPI, test with TestPyPI:

1. Create token on [TestPyPI](https://test.pypi.org/manage/account/)
2. Add as `TEST_PYPI_TOKEN` secret
3. Temporarily modify workflow to use TestPyPI:
   ```yaml
   - name: Publish to TestPyPI
     env:
       UV_PUBLISH_TOKEN: ${{ secrets.TEST_PYPI_TOKEN }}
     run: uv publish --publish-url https://test.pypi.org/legacy/
   ```

4. Trigger manually via GitHub Actions UI

### Manual Workflow Trigger

1. Go to Actions → "Publish to PyPI"
2. Click "Run workflow"
3. Select branch (usually `main`)
4. Click "Run workflow"

## How It Works

### Automatic Flow

1. **Commit with conventional message**:
   ```bash
   git commit -m "feat: add new output format"
   git push
   ```

2. **Version workflow runs**:
   - Determines version bump (MINOR for `feat:`)
   - Updates `pyproject.toml` 
   - Creates tag (e.g., `v0.4.0`)
   - Creates GitHub Release

3. **Publish workflow triggers automatically**:
   - Checks out code at release tag
   - Verifies version consistency
   - Builds package with `uv build`
   - Tests installation
   - Publishes to PyPI with `uv publish`

4. **Package is live**:
   - Available at https://pypi.org/project/glab-pipeviz/
   - Installable via `pip install glab-pipeviz` or `uv tool install glab-pipeviz`

## Troubleshooting

### "Version already exists" Error

This means the version is already on PyPI. Solutions:
- Ensure version was bumped in `pyproject.toml`
- Check if version workflow ran correctly
- PyPI doesn't allow re-uploading same version (even if deleted)

### "Authentication failed" Error

- Verify `PYPI_TOKEN` secret exists and is valid
- Check token hasn't expired
- Ensure token has correct scope (project or account)
- For project-scoped tokens, ensure project exists on PyPI

### Version Mismatch Error

The workflow enforces that the release tag version matches `pyproject.toml`:
- Release tag: `v0.4.0` → expects `version = "0.4.0"` in pyproject.toml
- If mismatch, the workflow fails before publishing
- Usually indicates the version workflow didn't run properly

### Build Fails

- Check `pyproject.toml` syntax is valid
- Ensure all files listed in `[tool.hatch.build.targets.sdist]` exist
- Verify dependencies are correctly specified

## Security Best Practices

1. ✅ **Use project-scoped tokens** (not account-scoped) when possible
2. ✅ **Use GitHub environments** for additional protection
3. ✅ **Consider migrating to Trusted Publishers** (no tokens to manage)
4. ✅ **Regularly rotate tokens** (every 6-12 months)
5. ✅ **Never commit tokens** to repository
6. ✅ **Use separate tokens** for TestPyPI and PyPI

## Monitoring

### Check Publication Status

- **GitHub Actions**: Repository → Actions → "Publish to PyPI"
- **PyPI Project**: https://pypi.org/project/glab-pipeviz/#history
- **Download Stats**: https://pypistats.org/packages/glab-pipeviz

### Verify Installation

After publication, test installation:
```bash
# With pip
pip install --upgrade glab-pipeviz

# With uv
uv tool upgrade glab-pipeviz

# Check version
glab-pipeviz --version
```

## Manual Publication (Emergency)

If automation fails, publish manually:

```bash
# Build
uv build

# Publish (with token from environment or keyring)
uv publish

# Or with explicit token
uv publish --token pypi-your-token-here

# Or to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/ --token pypi-your-test-token
```

## Resources

- [PyPI Help](https://pypi.org/help/)
- [uv Documentation - Publishing](https://docs.astral.sh/uv/guides/publish/)
- [GitHub Actions - PyPI Publishing](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
