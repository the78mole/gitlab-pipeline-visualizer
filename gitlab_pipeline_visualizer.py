#!/usr/bin/env python

import argparse
import base64
import json
import logging
import os
import re
import sys
import zlib
from collections import defaultdict
from pathlib import Path
from textwrap import dedent

import yaml

__version__ = "0.0.99"  # Development version, updated by CI/CD

logger = logging.getLogger("GitLabPipelineVisualizer")


DEFAULT_MERMAID_CONFIG = """\
gantt:
  useWidth: 1600
"""


def get_version():
    """Get package version from pyproject.toml or fallback to __version__."""
    try:
        # Try to read version from pyproject.toml
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, 'r') as f:
                for line in f:
                    if line.startswith('version = '):
                        # Extract version from: version = "0.3.0"
                        return line.split('"')[1]
    except Exception:
        pass
    
    # Fallback to module __version__
    return __version__


def setup_logging(verbose):
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


class GitLabCIParser:
    """Parse GitLab CI/CD YAML configuration files."""
    
    def __init__(self, yaml_path):
        """
        Initialize parser with a path to .gitlab-ci.yml file.
        
        Args:
            yaml_path: Path to the GitLab CI YAML file
        """
        self.yaml_path = Path(yaml_path).resolve()
        self.base_dir = self._find_repo_root()
        self.config = {}
        self.jobs = {}
        self.stages = []
    
    def _find_repo_root(self):
        """
        Find the Git repository root or fallback to YAML file's parent directory.
        GitLab CI 'local:' includes are relative to the repository root.
        """
        # Try to find .git directory by walking up the tree
        current = self.yaml_path.parent
        while current != current.parent:  # Stop at filesystem root
            if (current / '.git').exists():
                logger.debug(f"Found Git repository root: {current}")
                return current
            current = current.parent
        
        # Fallback to YAML file's parent directory
        logger.debug(f"No Git repository found, using YAML parent: {self.yaml_path.parent}")
        return self.yaml_path.parent
        
    def load_yaml(self, file_path):
        """Load and parse a YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            raise
    
    def resolve_includes(self, config, visited=None):
        """
        Recursively resolve 'include' directives in GitLab CI configuration.
        
        Args:
            config: The configuration dict to process
            visited: Set of already visited file paths to prevent circular includes
            
        Returns:
            Merged configuration with all includes resolved
        """
        if visited is None:
            visited = set()
            
        # Handle include directive
        if 'include' in config:
            includes = config.pop('include')
            
            # Normalize to list
            if not isinstance(includes, list):
                includes = [includes]
            
            for inc in includes:
                # Handle different include formats
                if isinstance(inc, str):
                    # Simple string path - strip leading slash to ensure relative path
                    include_path = self.base_dir / inc.lstrip('/')
                elif isinstance(inc, dict):
                    # Dict with 'local' key
                    if 'local' in inc:
                        # Strip leading slash to ensure relative path
                        include_path = self.base_dir / inc['local'].lstrip('/')
                    else:
                        # Skip remote includes (project, remote, template)
                        logger.warning(f"Skipping non-local include: {inc}")
                        continue
                else:
                    continue
                
                # Check for circular includes
                include_path = include_path.resolve()
                if include_path in visited:
                    logger.warning(f"Circular include detected: {include_path}")
                    continue
                    
                visited.add(include_path)
                
                if include_path.exists():
                    logger.info(f"Processing include: {include_path}")
                    included_config = self.load_yaml(include_path)
                    # Recursively resolve includes in the included file
                    included_config = self.resolve_includes(included_config, visited)
                    # Merge configurations (included config is applied first, then overridden)
                    config = {**included_config, **config}
                else:
                    logger.warning(f"Include file not found: {include_path}")
        
        return config
    
    def parse(self):
        """Parse the GitLab CI configuration."""
        logger.info(f"Parsing {self.yaml_path}")
        
        # Load main config
        self.config = self.load_yaml(self.yaml_path)
        
        # Resolve includes
        self.config = self.resolve_includes(self.config)
        
        # Extract stages
        self.stages = self.config.pop('stages', ['build', 'test', 'deploy'])
        logger.info(f"Stages: {self.stages}")
        
        # Reserved keywords that are not jobs
        reserved_keywords = {
            'default', 'variables', 'workflow', 'include', 'stages', 'before_script',
            'after_script', 'cache', 'image', 'services'
        }
        
        # Extract jobs (anything starting with '.' is a template/anchor)
        for name, job_config in self.config.items():
            if name.startswith('.') or name in reserved_keywords:
                continue
                
            if not isinstance(job_config, dict):
                continue
            
            # Extract job info
            job = {
                'name': name,
                'identifier': self.name_to_identifier(name),
                'stage': job_config.get('stage', self.stages[0] if self.stages else 'test'),
                'needs': [],
                'dependencies': [],
            }
            
            # Handle needs (DAG dependencies)
            if 'needs' in job_config:
                needs = job_config['needs']
                if isinstance(needs, list):
                    for need in needs:
                        if isinstance(need, str):
                            job['needs'].append(self.name_to_identifier(need))
                        elif isinstance(need, dict) and 'job' in need:
                            job['needs'].append(self.name_to_identifier(need['job']))
            
            self.jobs[job['identifier']] = job
            
        logger.info(f"Found {len(self.jobs)} jobs")
        return self.jobs, self.stages
    
    def name_to_identifier(self, name):
        """Convert job name to valid identifier."""
        return re.sub(r"\W+|^(?=\d)", "_", str(name))


class GitLabPipelineVisualizer:
    """Visualize GitLab CI/CD pipeline configuration as Mermaid diagrams."""
    
    def __init__(self, jobs, stages):
        """
        Initialize visualizer with parsed job data.
        
        Args:
            jobs: Dict of jobs with their configuration
            stages: List of stage names
        """
        self.jobs = jobs
        self.stages = stages
        
    def build_dependency_graph(self):
        """
        Build dependency graph based on needs and stages.
        
        Returns:
            dict: Graph where keys are job IDs and values are lists of dependency job IDs
        """
        dependencies = {}
        
        # Create mapping of stages to jobs
        stage_jobs = defaultdict(list)
        for job_id, job in self.jobs.items():
            stage_jobs[job['stage']].append(job_id)
        
        for job_id, job in self.jobs.items():
            if job['needs']:
                # Explicit needs/dependencies
                dependencies[job_id] = job['needs']
            else:
                # Implicit stage-based dependencies
                deps = []
                try:
                    stage_idx = self.stages.index(job['stage'])
                    if stage_idx > 0:
                        # Depend on all jobs from previous stage
                        prev_stage = self.stages[stage_idx - 1]
                        deps = stage_jobs.get(prev_stage, [])
                except ValueError:
                    # Stage not in list, no dependencies
                    pass
                dependencies[job_id] = deps
        
        return dependencies
    
    def generate_mermaid_dependencies(self):
        """Generate a Mermaid state diagram showing job dependencies."""
        dependencies = self.build_dependency_graph()
        
        mermaid = [
            "stateDiagram-v2",
            "",
            "    %% Style definitions",
            '    classDef jobStyle fill:#e8f4f8,stroke:#0366d6,color:#000',
            "",
            '    state "Pipeline Dependencies" as pipeline {',
            "",
            "    %% Jobs",
        ]
        
        # Add job states
        for job_id, job in self.jobs.items():
            stage = job['stage']
            mermaid.append(f'    state "{job["name"]} ({stage})" as {job_id}')
        
        mermaid.append("")
        mermaid.append("    %% Dependencies")
        
        # Add dependencies
        for job_id in self.jobs:
            job_deps = dependencies.get(job_id, [])
            if not job_deps:
                # No dependencies - starts from beginning
                mermaid.append(f"    [*] --> {job_id}")
            else:
                for dep in job_deps:
                    if dep in self.jobs:
                        mermaid.append(f"    {dep} --> {job_id}")
        
        mermaid.append("    }")
        
        # Apply styling
        for job_id in self.jobs:
            mermaid.append(f"class {job_id} jobStyle")
        
        return "\n".join(mermaid)
    
    def generate_mermaid_stages(self):
        """Generate a Mermaid flowchart showing stages and jobs."""
        mermaid = [
            "graph LR",
            "",
            "    %% Style definitions",
            '    classDef stageStyle fill:#f0f0f0,stroke:#333,stroke-width:2px',
            '    classDef jobStyle fill:#e8f4f8,stroke:#0366d6',
            "",
        ]
        
        # Group jobs by stage
        stage_jobs = defaultdict(list)
        for job_id, job in self.jobs.items():
            stage_jobs[job['stage']].append((job_id, job['name']))
        
        # Create subgraphs for each stage
        for stage in self.stages:
            if stage in stage_jobs:
                stage_id = self.name_to_identifier(stage)
                mermaid.append(f"    subgraph {stage_id}[{stage}]")
                for job_id, job_name in stage_jobs[stage]:
                    mermaid.append(f'        {job_id}["{job_name}"]')
                mermaid.append("    end")
                mermaid.append("")
        
        # Connect stages
        for i in range(len(self.stages) - 1):
            stage1_id = self.name_to_identifier(self.stages[i])
            stage2_id = self.name_to_identifier(self.stages[i + 1])
            mermaid.append(f"    {stage1_id} --> {stage2_id}")
        
        return "\n".join(mermaid)
    
    def generate_mermaid_content(self, mode="deps"):
        """
        Generate Mermaid diagram content.
        
        Args:
            mode: Visualization mode - "deps" or "stages"
            
        Returns:
            str: Mermaid diagram markup
        """
        if mode == "stages":
            return self.generate_mermaid_stages()
        else:
            return self.generate_mermaid_dependencies()
    
    def generate_mermaid(self, content, config):
        """Generate complete Mermaid diagram with config."""
        parts = []
        if config:
            parts.append("---")
            parts.append("config:")
            parts.append(dedent(config).strip())
            parts.append("---")
        parts.append(content)
        return "\n".join(parts)
    
    def generate_mermaid_live_url(self, content, config, mode="view"):
        """Generate URL for mermaid.live."""
        mermaid_doc = self.generate_mermaid(content, config)
        
        # Create JSON document
        json_doc = json.dumps({"code": mermaid_doc, "mermaid": "{}", "updateEditor": False})
        
        # Encode
        encoded = base64.b64encode(json_doc.encode()).decode()
        
        if mode == "edit":
            return f"https://mermaid.live/edit#base64:{encoded}"
        else:
            return f"https://mermaid.live/view#base64:{encoded}"
    
    def generate_mermaid_ink_url(self, content, config, format_type="png"):
        """Generate URL for mermaid.ink."""
        mermaid_doc = self.generate_mermaid(content, config)
        
        # Encode
        encoded = base64.b64encode(mermaid_doc.encode()).decode()
        
        return f"https://mermaid.ink/img/{encoded}?type={format_type}"
    
    def name_to_identifier(self, name):
        """Convert name to valid identifier."""
        return re.sub(r"\W+|^(?=\d)", "_", str(name))


def open_url_in_browser(url):
    """Open URL in default web browser."""
    try:
        import webbrowser
        webbrowser.open(url)
        logger.info(f"Opened URL in browser: {url}")
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="""
Visualize GitLab CI/CD pipeline configuration as a Mermaid diagram.

Reads local .gitlab-ci.yml files and generates visualization of the pipeline structure.

Two visualization modes are available:
- deps: shows dependencies between jobs (default)
- stages: shows stages and jobs grouped by stage

Usage examples:
    glab-pipeviz .gitlab-ci.yml
    glab-pipeviz main_pipeline.yaml --mode stages
    glab-pipeviz .gitlab-ci.yml --output view --open
""",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=f"""
A default Mermaid configuration is provided:
{DEFAULT_MERMAID_CONFIG}

Example .gitlab-ci.yml structure:
--------------------------------
stages:
  - build
  - test
  - deploy

build:job:
  stage: build
  script:
    - echo "Building..."

test:unit:
  stage: test
  needs: [build:job]
  script:
    - echo "Testing..."

deploy:production:
  stage: deploy
  needs: [test:unit]
  script:
    - echo "Deploying..."
--------------------------------
""",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    parser.add_argument(
        "yaml_file",
        help="Path to GitLab CI YAML file (e.g., .gitlab-ci.yml, main_pipeline.yaml)",
    )
    parser.add_argument(
        "--mode",
        choices=["deps", "stages"],
        default="deps",
        help="visualization mode: deps (default) shows job dependencies, stages shows stage grouping",
    )
    parser.add_argument(
        "--output",
        choices=["raw", "view", "edit", "jpg", "png", "svg", "webp", "pdf"],
        default="raw",
        help="""output format:
- raw: raw mermaid document (default)
- view: URL to view diagram on mermaid.live
- edit: URL to edit diagram on mermaid.live
- jpg: URL of jpg image on mermaid.ink
- png: URL of png image on mermaid.ink
- webp: URL for webp image on mermaid.ink
- svg: URL for svg image on mermaid.ink
- pdf: URL for pdf on mermaid.ink""",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="open the URL in your default web browser (only valid with URL outputs)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase verbosity (use -v for info, -vv for debug)",
    )

    args = parser.parse_args()

    # Validate --open usage
    if args.open and args.output == "raw":
        parser.error("--open option can only be used with URL outputs")

    try:
        setup_logging(args.verbose)

        # Parse YAML file
        parser_obj = GitLabCIParser(args.yaml_file)
        jobs, stages = parser_obj.parse()

        if not jobs:
            print("Error: No jobs found in the pipeline configuration", file=sys.stderr)
            sys.exit(1)

        # Create visualizer
        visualizer = GitLabPipelineVisualizer(jobs, stages)

        # Get the mermaid diagram content
        mermaid_content = visualizer.generate_mermaid_content(args.mode)
        mermaid_config = DEFAULT_MERMAID_CONFIG

        # Handle different output formats
        url = None
        if args.output in ("edit", "view"):
            url = visualizer.generate_mermaid_live_url(
                mermaid_content, mermaid_config, args.output
            )
            print(url)
        elif args.output in ("jpg", "png", "webp", "svg", "pdf"):
            url = visualizer.generate_mermaid_ink_url(
                mermaid_content, mermaid_config, args.output
            )
            print(url)
        else:
            print(visualizer.generate_mermaid(mermaid_content, mermaid_config))

        # Open URL in browser if requested
        if args.open and url:
            open_url_in_browser(url)

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose >= 2:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
