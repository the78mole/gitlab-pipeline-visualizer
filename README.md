# GitLab Pipeline Visualizer

Visualize GitLab CI/CD pipeline configurations as Mermaid diagrams by analyzing local `.gitlab-ci.yml` files.

> **Note:** This tool is based on the [original gitlab-pipeline-visualizer](https://github.com/twidi/gitlab-pipeline-visualizer) by Stéphane 'Twidi' Angel and has been significantly rewritten. The original version used GitLab's GraphQL API to fetch and visualize actual pipeline executions. This version focuses on **local YAML file analysis** without requiring API access, making it perfect for offline development and CI/CD configuration validation.

## Quick Start

```bash
# Install via uv (recommended)
uv tool install glab-pipeviz

# Or via pip
pip install glab-pipeviz

# Visualize your pipeline
glab-pipeviz .gitlab-ci.yml
```

## Features

- **Local YAML file analysis**: No API access required - works entirely with local files
- **Include support**: Automatically resolves `include:` directives (local files)
- Two visualization modes:
  - **Dependencies**: Shows job dependencies and execution flow (default)
  - **Stages**: Shows pipeline stages with grouped jobs
- Multiple output formats:
  - Raw Mermaid diagram
  - Interactive URLs for mermaid.live (view/edit)
  - Image URLs from mermaid.ink (png, jpg, svg, webp, pdf)
- Simple CLI interface

## Installation

### Option 1: Using uv (recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package installer and resolver. It's the recommended way to install and manage this tool.

**Install uv first** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Install glab-pipeviz as a tool**:
```bash
uv tool install glab-pipeviz
```

This installs the tool in an isolated environment with all dependencies. The `glab-pipeviz` command will be available globally.

**Install from source**:
```bash
git clone https://github.com/twidi/gitlab-pipeline-visualizer.git
cd gitlab-pipeline-visualizer
uv tool install .
```

**Upgrade to latest version**:
```bash
uv tool upgrade glab-pipeviz
```

**Uninstall**:
```bash
uv tool uninstall glab-pipeviz
```

### Option 2: Using pip

Standard installation via pip:
```bash
pip install glab-pipeviz
```

**Upgrade to latest version**:
```bash
pip install --upgrade glab-pipeviz
```

**Install in user directory** (no root required):
```bash
pip install --user glab-pipeviz
```

**Install in virtual environment** (recommended for development):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install glab-pipeviz
```

### Option 3: For Development

If you want to contribute or modify the code:

```bash
# Clone repository
git clone https://github.com/twidi/gitlab-pipeline-visualizer.git
cd gitlab-pipeline-visualizer

# Using uv (recommended)
uv sync

# Or using pip with editable install
pip install -e .
```

## Usage

### Basic Usage

```bash
glab-pipeviz <path-to-yaml-file> [options]
```

The tool accepts any GitLab CI/CD configuration file (`.gitlab-ci.yml`, `main_pipeline.yaml`, etc.).

### Examples

**1. Generate dependency graph (default mode)**
```bash
glab-pipeviz .gitlab-ci.yml
```
Outputs a Mermaid state diagram showing job dependencies and execution order.

**2. Generate stages overview**
```bash
glab-pipeviz .gitlab-ci.yml --mode stages
```
Outputs a Mermaid flow diagram with jobs grouped by stages.

**3. Open interactive diagram in browser**
```bash
glab-pipeviz .gitlab-ci.yml --output view --open
```
Opens the diagram in mermaid.live for interactive viewing.

**4. Get a PNG image URL**
```bash
glab-pipeviz .gitlab-ci.yml --output png
```
Returns a URL to a PNG rendering of the diagram via mermaid.ink.

**5. Edit diagram interactively**
```bash
glab-pipeviz .gitlab-ci.yml --mode stages --output edit --open
```
Opens the diagram in mermaid.live's editor for customization.

**6. Save to file**
```bash
glab-pipeviz .gitlab-ci.yml > pipeline.mmd
glab-pipeviz .gitlab-ci.yml --mode stages > stages.mmd
```

**7. Embed in Markdown**
```bash
echo '```mermaid' > PIPELINE.md
glab-pipeviz .gitlab-ci.yml --mode stages >> PIPELINE.md
echo '```' >> PIPELINE.md
```
Creates a markdown file with embedded Mermaid diagram (auto-rendered on GitHub/GitLab).

**8. Work with custom filenames**
```bash
glab-pipeviz my-pipeline.yaml
glab-pipeviz ci/config/main.yml
glab-pipeviz ../other-project/.gitlab-ci.yml
```

**9. Verbose output for debugging**
```bash
glab-pipeviz .gitlab-ci.yml -v        # Info logging
glab-pipeviz .gitlab-ci.yml -vv       # Debug logging
```

**10. Running from source without installation**
```bash
# With uv
uv run python gitlab_pipeline_visualizer.py .gitlab-ci.yml

# With system Python
python gitlab_pipeline_visualizer.py .gitlab-ci.yml
```

### Command Line Options

```
positional arguments:
  yaml_file             Path to GitLab CI YAML file

options:
  -h, --help            Show help message and exit
  
  --mode {deps,stages}  Visualization mode:
                        • deps: Job dependencies graph (default)
                        • stages: Stage grouping diagram
  
  --output {raw,view,edit,jpg,png,svg,webp,pdf}
                        Output format:
                        • raw: Raw Mermaid document (default)
                        • view: URL to view on mermaid.live
                        • edit: URL to edit on mermaid.live
                        • jpg, png, svg, webp, pdf: Image URL from mermaid.ink
  
  --open                Open URL in default browser
                        (only works with view, edit, and image outputs)
  
  -v, --verbose         Increase verbosity:
                        • -v: Info level logging
                        • -vv: Debug level logging
```

### Output Formats Explained

#### `raw` (default)
Outputs the raw Mermaid diagram syntax. Use this for:
- Saving to `.mmd` files
- Embedding in Markdown (GitHub, GitLab, Notion, Confluence)
- Processing with mermaid-cli (`mmdc`)
- VS Code Mermaid extensions

#### `view` and `edit`
Generates URLs for mermaid.live:
- `view`: Read-only rendering
- `edit`: Interactive editor with customization options

The diagram is encoded in the URL itself (no upload required).

#### Image formats (`png`, `jpg`, `svg`, `webp`, `pdf`)
Generates mermaid.ink URLs that render diagrams as images:
- **PNG/JPG**: Raster images, good for embedding in documents
- **SVG**: Vector graphics, best quality for any size
- **WebP**: Modern compressed format
- **PDF**: Print-ready documents

These URLs are **direct links** to the rendered images, perfect for:
- README badges
- Documentation
- Presentations
- Sharing via chat/email

## Example Pipeline Configuration

The tool analyzes your `.gitlab-ci.yml` file:

```yaml
stages:
  - build
  - test
  - deploy

variables:
  DOCKER_IMAGE: myapp:latest

build:docker:
  stage: build
  script:
    - docker build -t $DOCKER_IMAGE .

test:unit:
  stage: test
  needs: [build:docker]
  script:
    - pytest tests/unit/

test:integration:
  stage: test
  needs: [build:docker]
  script:
    - pytest tests/integration/

deploy:staging:
  stage: deploy
  needs:
    - test:unit
    - test:integration
  script:
    - kubectl apply -f k8s/staging/
  environment:
    name: staging
```

### Include Support

The tool automatically resolves local `include:` directives:

```yaml
# .gitlab-ci.yml
include:
  - local: 'ci/build.yml'
  - local: 'ci/test.yml'
  - local: 'ci/deploy.yml'

stages:
  - build
  - test
  - deploy
```

**Note:** Only local includes are supported. Remote includes (`project:`, `remote:`, `template:`) are skipped with a warning.

## How It Works

1. **Parse**: Reads your `.gitlab-ci.yml` file and resolves local includes
2. **Analyze**: Extracts jobs, stages, and dependencies (`needs:` relationships)
3. **Visualize**: Generates Mermaid diagram showing:
   - Job dependencies (deps mode): Directed graph showing execution order
   - Stage grouping (stages mode): Jobs grouped by their stage

## Requirements

- Python 3.8+
- PyYAML for YAML parsing

## Development

### Running Tests

```bash
# Install development dependencies
uv sync

# Run tests
uv run pytest -v
```

### Building the Package

```bash
uv build
```

## Differences from Original Version

The original [gitlab-pipeline-visualizer](https://github.com/twidi/gitlab-pipeline-visualizer) by Stéphane 'Twidi' Angel was a Flask web application that used GitLab's GraphQL API to fetch and visualize actual pipeline executions with timing data.

**This rewritten version:**
- ✅ Works **offline** with local `.gitlab-ci.yml` files
- ✅ No API access or authentication required
- ✅ Simple CLI tool (no web server needed)
- ✅ Analyzes pipeline **configuration** (not execution data)
- ✅ Perfect for CI/CD development and validation
- ✅ Lightweight (only dependency: PyYAML)

**What it doesn't do:**
- ❌ Make API calls to GitLab
- ❌ Show actual pipeline execution times
- ❌ Display job durations or timestamps
- ❌ Show pipeline status or job results
- ❌ Require authentication tokens or project access

### Use Cases

**This version** (local YAML analysis):
- Validate pipeline structure before committing
- Understand complex includes and dependencies
- Document CI/CD architecture
- Offline development
- Quick visualization during pipeline design

**Original version** (API-based):
- Analyze completed pipeline executions
- Review job timing and performance
- Investigate pipeline bottlenecks
- Historical execution data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Commit Message Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automatic semantic versioning:

- **Any commit** → PATCH bump (0.0.+1)
- **`feat:`** → MINOR bump (0.+1.0)  
- **`BREAKING CHANGE:` or `!`** → MAJOR bump (+1.0.0)

Examples:
```bash
# Patch bump
git commit -m "fix: resolve parsing error"
git commit -m "docs: update readme"

# Minor bump  
git commit -m "feat: add SVG output support"
git commit -m "feat(cli): add --open flag"

# Major bump
git commit -m "feat!: remove deprecated API"
git commit -m "refactor: rewrite parser

BREAKING CHANGE: Parser API has changed"
```

See [.github/COMMIT_CONVENTION.md](.github/COMMIT_CONVENTION.md) for detailed guidelines.

## Development Workflows

This project uses automated workflows for versioning and publication:

- **Semantic Versioning**: Automatic version bumps based on conventional commits (see [.github/COMMIT_CONVENTION.md](.github/COMMIT_CONVENTION.md))
- **PyPI Publication**: Automatic publishing to PyPI when releases are created (see [.github/PYPI_SETUP.md](.github/PYPI_SETUP.md))

## License

MIT License - see LICENSE file for details.

## Authors

- Stéphane 'Twidi' Angel - Original concept
- Daniel (the78mole) Glaser - Local YAML implementation

## Links

- Repository: https://github.com/twidi/gitlab-pipeline-visualizer
- Issues: https://github.com/twidi/gitlab-pipeline-visualizer/issues
- PyPI: https://pypi.org/project/glab-pipeviz/
