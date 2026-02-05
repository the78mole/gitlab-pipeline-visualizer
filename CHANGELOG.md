# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-02-05

### Changed - Major Rewrite
- **Complete architecture change**: Tool now parses local `.gitlab-ci.yml` files instead of making GitLab API calls
- Tool works entirely offline with local YAML files
- Removed all GitLab API integration code
- Removed Flask web interface and related dependencies
- Removed Git repository integration

### Added
- Local YAML file parsing with PyYAML
- Support for `include:` directives (local files only)
- `GitLabCIParser` class for parsing pipeline configurations
- Automatic resolution of local includes with circular dependency detection
- Two visualization modes:
  - `deps`: Dependency graph (default)
  - `stages`: Stage-grouped view
- Better error handling for YAML parsing errors

### Removed
- All GitLab API calls and `requests` dependency
- Flask web interface (`app.py`, templates)
- `flask` and `flask-cors` dependencies
- Git remote detection functionality
- Token-based authentication
- Pipeline execution data  visualization (times, status, durations)
- Browser addon references

### Technical
- New dependency: `pyyaml>=5.0.0`
- Removed dependencies: `requests`, `flask`, `flask-cors`
- Simplified CLI interface focused on local file paths
- Package now contains only `gitlab_pipeline_visualizer.py`

## [0.2.0] - 2026-02-05

### Added
- Local Git repository integration
- Automatic GitLab information extraction from Git remotes
- Support for both SSH and HTTPS Git remote URLs
- `--remote` option to specify Git remote
- Comprehensive test suite for Git integration

### Changed
- Primary argument from `url` to `pipeline_ref`
- Enhanced help text with usage examples

## [0.1.0] - 2026-02-05

### Added
- Initial release with uv and pyproject.toml support
- Package name: `glab-pipeviz`
- CLI entry point: `glab-pipeviz`
- MIT License
- GitHub Actions workflow for CI/CD
- Support for Python 3.8+
