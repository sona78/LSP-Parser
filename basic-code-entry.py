#!/usr/bin/env python3
"""
GitHub Repository Code Analysis Entry Point

This is the main entry point for analyzing GitHub repositories using the
complete Lynx parser pipeline: parsing, visualization, and AI description.

Features:
- Clone GitHub repositories
- Run multilspy parser to extract code structure
- Generate interactive React visualizations
- Provide AI-powered code descriptions via Gemini

Usage:
    python basic-code-entry.py
    
Or programmatically:
    from basic_code_entry import GitHubCodeAnalyzer
    analyzer = GitHubCodeAnalyzer()
    analyzer.analyze_repository("https://github.com/user/repo")
"""

import os
import sys
import shutil
import subprocess
import tempfile
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import argparse


class GitHubCodeAnalyzer:
    """Main class for analyzing GitHub repositories with the complete pipeline."""
    
    def __init__(self, workspace_dir: str = "./workspace"):
        """
        Initialize the GitHub code analyzer.
        
        Args:
            workspace_dir: Directory to use for temporary workspaces
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        
        # Ensure all required scripts are available
        self.parser_script = Path("basic-parser.py")
        self.describer_script = Path("basic-describer.py")
        self.react_app_dir = Path("react-graph-viewer")
        
        self._validate_dependencies()
        
    def _validate_dependencies(self):
        """Validate that all required components are available."""
        missing = []
        
        if not self.parser_script.exists():
            missing.append("basic-parser.py")
        if not self.describer_script.exists():
            missing.append("basic-describer.py")
        if not self.react_app_dir.exists():
            missing.append("react-graph-viewer directory")
            
        if missing:
            raise FileNotFoundError(
                f"Missing required components: {', '.join(missing)}. "
                "Please ensure all components are in the current directory."
            )
            
    def clone_repository(self, github_url: str, target_dir: Path) -> bool:
        """
        Clone a GitHub repository to the target directory.
        
        Args:
            github_url: GitHub repository URL
            target_dir: Directory to clone into
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Cloning repository: {github_url}")
        
        # Validate GitHub URL
        parsed = urlparse(github_url)
        if not parsed.hostname or 'github.com' not in parsed.hostname:
            print(f"Error: Invalid GitHub URL: {github_url}")
            return False
            
        # Remove existing directory if it exists
        if target_dir.exists():
            def remove_readonly(func, path, _):
                """Clear readonly bit and reattempt removal."""
                import stat
                os.chmod(path, stat.S_IWRITE)
                func(path)
            
            shutil.rmtree(target_dir, onerror=remove_readonly)
            
        try:
            # Clone the repository
            result = subprocess.run([
                'git', 'clone', '--depth', '1', github_url, str(target_dir)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"Error cloning repository: {result.stderr}")
                return False
                
            print(f"Successfully cloned repository to {target_dir}")
            return True
            
        except subprocess.TimeoutExpired:
            print("Error: Repository cloning timed out")
            return False
        except FileNotFoundError:
            print("Error: Git is not installed or not in PATH")
            return False
        except Exception as e:
            print(f"Error cloning repository: {e}")
            return False
            
    def get_repo_info(self, github_url: str) -> Dict[str, str]:
        """Extract repository information from GitHub URL."""
        parsed = urlparse(github_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo_name = path_parts[1].replace('.git', '')
            return {
                'owner': owner,
                'repo_name': repo_name,
                'full_name': f"{owner}/{repo_name}",
                'url': github_url
            }
        else:
            return {
                'owner': 'unknown',
                'repo_name': 'repository',
                'full_name': 'unknown/repository',
                'url': github_url
            }
            
    def find_python_files(self, directory: Path) -> int:
        """Count Python files in the directory."""
        python_files = list(directory.glob("**/*.py"))
        return len(python_files)
        
    def run_parser(self, repo_dir: Path) -> bool:
        """
        Run the basic-parser.py on the cloned repository.
        
        Args:
            repo_dir: Directory containing the cloned repository
            
        Returns:
            True if parsing succeeded, False otherwise
        """
        print(f"Running parser on {repo_dir}")
        
        # Count Python files
        python_count = self.find_python_files(repo_dir)
        if python_count == 0:
            print("Warning: No Python files found in repository")
            return False
            
        print(f"Found {python_count} Python files to analyze")
        
        try:
            # Modify the parser script to use the new repository path
            with open(self.parser_script, 'r') as f:
                parser_code = f.read()
                
            # Replace the repository_root_path
            original_path = 'repository_root_path = os.path.abspath("test-project")'
            new_path = f'repository_root_path = os.path.abspath("{repo_dir}")'
            
            if original_path in parser_code:
                modified_code = parser_code.replace(original_path, new_path)
                
                # Write temporary parser script
                temp_parser = Path("temp_parser.py")
                with open(temp_parser, 'w') as f:
                    f.write(modified_code)
                    
                # Run the modified parser
                result = subprocess.run([
                    sys.executable, str(temp_parser)
                ], capture_output=True, text=True, timeout=600)
                
                # Clean up temporary file
                temp_parser.unlink()
                
                if result.returncode != 0:
                    print(f"Parser failed: {result.stderr}")
                    return False
                    
                print("Parser completed successfully")
                return True
            else:
                print("Error: Could not modify parser script")
                return False
                
        except Exception as e:
            print(f"Error running parser: {e}")
            return False
            
    def build_react_app(self) -> bool:
        """Build the React visualization app."""
        print("Building React visualization app...")
        
        if not self.react_app_dir.exists():
            print("Error: React app directory not found")
            return False
            
        try:
            # Check if node_modules exists, run npm install if not
            node_modules = self.react_app_dir / "node_modules"
            if not node_modules.exists():
                print("Installing npm dependencies...")
                result = subprocess.run([
                    'npm', 'install'
                ], cwd=self.react_app_dir, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    print(f"npm install failed: {result.stderr}")
                    return False
                    
            # Build the app
            print("Building React app...")
            result = subprocess.run([
                'npm', 'run', 'build'
            ], cwd=self.react_app_dir, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"React build failed: {result.stderr}")
                return False
                
            print("React app built successfully")
            return True
            
        except Exception as e:
            print(f"Error building React app: {e}")
            return False
            
    def start_describer(self, repo_dir: Path, gemini_api_key: Optional[str] = None) -> bool:
        """
        Start the describer for the analyzed repository.
        
        Args:
            repo_dir: Directory containing the analyzed repository
            gemini_api_key: Optional Gemini API key for AI features
            
        Returns:
            True if describer started successfully
        """
        print("Setting up code describer...")
        
        try:
            # Import and initialize the describer
            sys.path.insert(0, '.')
            
            # Read and execute the describer script with modified paths
            with open(self.describer_script, 'r') as f:
                describer_code = f.read()
                
            # Replace the default repository path
            original_repo_path = 'repository_path: str = "./test-project"'
            new_repo_path = f'repository_path: str = "{repo_dir}"'
            
            if original_repo_path in describer_code:
                modified_code = describer_code.replace(original_repo_path, new_repo_path)
                
                # Execute the modified code
                local_vars = {}
                exec(modified_code, globals(), local_vars)
                
                # Initialize the describer
                CodeGraphDescriber = local_vars['CodeGraphDescriber']
                describer = CodeGraphDescriber()
                
                # Setup Gemini API if key provided
                if gemini_api_key:
                    success = describer.setup_gemini_api(gemini_api_key)
                    if success:
                        print("Gemini AI initialized successfully")
                    else:
                        print("Warning: Gemini AI initialization failed")
                        
                print("Code describer ready!")
                return True
                
            else:
                print("Error: Could not modify describer script")
                return False
                
        except Exception as e:
            print(f"Error setting up describer: {e}")
            return False
            
    def analyze_repository(self, github_url: str, gemini_api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the complete analysis pipeline on a GitHub repository.
        
        Args:
            github_url: GitHub repository URL
            gemini_api_key: Optional Gemini API key for AI features
            
        Returns:
            Dictionary with analysis results and status
        """
        print("=" * 60)
        print("GITHUB REPOSITORY ANALYSIS")
        print("=" * 60)
        
        # Get repository info
        repo_info = self.get_repo_info(github_url)
        print(f"Repository: {repo_info['full_name']}")
        print(f"URL: {repo_info['url']}")
        
        # Create workspace for this repository
        repo_workspace = self.workspace_dir / repo_info['repo_name']
        
        results = {
            'repo_info': repo_info,
            'workspace': str(repo_workspace),
            'stages': {
                'clone': False,
                'parse': False,
                'visualize': False,
                'describe': False
            },
            'artifacts': {},
            'errors': []
        }
        
        try:
            # Stage 1: Clone repository
            print(f"\n1. Cloning repository...")
            if self.clone_repository(github_url, repo_workspace):
                results['stages']['clone'] = True
                print("✓ Repository cloned successfully")
            else:
                results['errors'].append("Failed to clone repository")
                return results
                
            # Stage 2: Run parser
            print(f"\n2. Parsing code structure...")
            if self.run_parser(repo_workspace):
                results['stages']['parse'] = True
                print("✓ Code parsing completed")
                
                # Check for generated artifacts
                artifacts_dir = Path("react-graph-viewer/public/artifacts")
                if artifacts_dir.exists():
                    for artifact_file in artifacts_dir.glob("*.json"):
                        with open(artifact_file, 'r') as f:
                            data = json.load(f)
                            results['artifacts'][artifact_file.stem] = {
                                'path': str(artifact_file),
                                'nodes': len(data.get('nodes', [])),
                                'edges': len(data.get('edges', []))
                            }
            else:
                results['errors'].append("Failed to parse code structure")
                return results
                
            # Stage 3: Build visualization
            print(f"\n3. Building visualization...")
            if self.build_react_app():
                results['stages']['visualize'] = True
                print("✓ Visualization built successfully")
            else:
                results['errors'].append("Failed to build visualization")
                # Continue anyway - visualization is optional
                
            # Stage 4: Setup describer
            print(f"\n4. Setting up AI describer...")
            if self.start_describer(repo_workspace, gemini_api_key):
                results['stages']['describe'] = True
                print("✓ AI describer ready")
            else:
                results['errors'].append("Failed to setup describer")
                # Continue anyway - describer is optional
                
            # Summary
            print(f"\n" + "=" * 60)
            print("ANALYSIS COMPLETE")
            print("=" * 60)
            
            successful_stages = sum(results['stages'].values())
            print(f"Completed {successful_stages}/4 stages successfully")
            
            if results['artifacts']:
                print(f"\nGenerated artifacts:")
                for name, info in results['artifacts'].items():
                    print(f"  - {name}: {info['nodes']} nodes, {info['edges']} edges")
                    
            if successful_stages >= 2:  # At least clone and parse succeeded
                print(f"\nNext steps:")
                print(f"  1. Run: python basic-describer.py")
                print(f"  2. Use 'extract' command to get detailed info")
                print(f"  3. Use 'describe <node_id>' for AI descriptions")
                if results['stages']['visualize']:
                    print(f"  4. Open react-graph-viewer/build/index.html for visualization")
                    
            return results
            
        except Exception as e:
            results['errors'].append(f"Unexpected error: {e}")
            print(f"Error: {e}")
            return results


def interactive_mode():
    """Run the analyzer in interactive mode."""
    print("GitHub Repository Code Analyzer")
    print("=" * 40)
    
    # Get GitHub URL
    github_url = input("Enter GitHub repository URL: ").strip()
    if not github_url:
        print("Error: No URL provided")
        return
        
    # Get optional Gemini API key
    gemini_key = input("Enter Gemini API key (optional, press Enter to skip): ").strip()
    if not gemini_key:
        gemini_key = None
        
    # Run analysis
    analyzer = GitHubCodeAnalyzer()
    results = analyzer.analyze_repository(github_url, gemini_key)
    
    # Show final results
    if results['errors']:
        print(f"\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
    else:
        print(f"\nAnalysis completed successfully!")
        

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Analyze GitHub repositories with Lynx parser')
    parser.add_argument('url', nargs='?', help='GitHub repository URL')
    parser.add_argument('--api-key', help='Gemini API key for AI features')
    parser.add_argument('--workspace', default='./workspace', help='Workspace directory')
    
    args = parser.parse_args()
    
    try:
        analyzer = GitHubCodeAnalyzer(args.workspace)
        
        if args.url:
            # Command line mode
            print(f"Analyzing repository: {args.url}")
            results = analyzer.analyze_repository(args.url, args.api_key)
            
            if results['errors']:
                print("Analysis completed with errors:")
                for error in results['errors']:
                    print(f"  - {error}")
                sys.exit(1)
            else:
                print("Analysis completed successfully!")
                
        else:
            # Interactive mode
            interactive_mode()
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()