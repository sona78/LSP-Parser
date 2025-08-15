#!/usr/bin/env python3
"""
Demo script for GitHub repository analysis.

This demonstrates the complete pipeline using a small public repository.
"""

import os
import sys
from pathlib import Path

# Import our analyzer
exec(open('basic-code-entry.py').read().replace('if __name__ == "__main__":', 'if False:'))

def demo_analysis():
    """Demonstrate GitHub repository analysis."""
    print("=" * 60)
    print("DEMO: GitHub Repository Analysis")
    print("=" * 60)
    
    # Use a small, simple Python repository for demo
    demo_repos = [
        "https://github.com/psf/requests",  # Well-known Python library
        "https://github.com/python/cpython", # Python itself (large)
        "https://github.com/pallets/flask",   # Flask web framework
    ]
    
    print("Available demo repositories:")
    for i, repo in enumerate(demo_repos, 1):
        repo_info = GitHubCodeAnalyzer().get_repo_info(repo)
        print(f"  {i}. {repo_info['full_name']}")
    
    print(f"  {len(demo_repos) + 1}. Enter custom URL")
    
    choice = input(f"\nSelect repository (1-{len(demo_repos) + 1}): ").strip()
    
    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(demo_repos):
            selected_url = demo_repos[choice_num - 1]
        elif choice_num == len(demo_repos) + 1:
            selected_url = input("Enter GitHub repository URL: ").strip()
        else:
            print("Invalid choice")
            return
    except ValueError:
        print("Invalid choice")
        return
    
    if not selected_url:
        print("No URL provided")
        return
    
    # Ask for API key
    api_key = input("Enter Gemini API key (optional, press Enter to skip): ").strip()
    if not api_key:
        api_key = None
    
    print(f"\nStarting analysis of: {selected_url}")
    print("This may take a few minutes depending on repository size...")
    
    try:
        # Initialize analyzer
        analyzer = GitHubCodeAnalyzer(workspace_dir="./demo-workspace")
        
        # Run analysis
        results = analyzer.analyze_repository(selected_url, api_key)
        
        # Show results
        print("\n" + "=" * 60)
        print("DEMO RESULTS")
        print("=" * 60)
        
        print(f"Repository: {results['repo_info']['full_name']}")
        print(f"Workspace: {results['workspace']}")
        
        stages = results['stages']
        print(f"\nStages completed:")
        for stage, success in stages.items():
            status = "[OK]" if success else "[FAIL]"
            print(f"  {status} {stage.title()}")
        
        if results['artifacts']:
            print(f"\nGenerated artifacts:")
            for name, info in results['artifacts'].items():
                print(f"  - {name}: {info['nodes']} nodes, {info['edges']} edges")
        
        if results['errors']:
            print(f"\nErrors encountered:")
            for error in results['errors']:
                print(f"  - {error}")
        
        # Show next steps
        successful_stages = sum(stages.values())
        if successful_stages >= 2:
            print(f"\nNext steps:")
            print(f"  1. Explore with: python basic-describer.py")
            print(f"  2. Interactive commands available:")
            print(f"     - list FUNCTION    # Show all functions")
            print(f"     - search <name>    # Find specific components")
            print(f"     - describe <id>    # AI description (if API key provided)")
            
            if stages['visualize']:
                print(f"  3. View visualization: react-graph-viewer/build/index.html")
        
        print(f"\nDemo completed!")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo failed: {e}")

if __name__ == "__main__":
    demo_analysis()