#!/usr/bin/env python3
"""
Test script for debugging demo-github-analysis.py with option 1 selected.
"""

import os
import sys
from pathlib import Path

# Import our analyzer
exec(open('basic-code-entry.py').read().replace('if __name__ == "__main__":', 'if False:'))

def test_option_1():
    """Test analysis with option 1 (psf/requests)."""
    print("=" * 60)
    print("TEST: GitHub Repository Analysis - Option 1")
    print("=" * 60)
    
    # Automatically select option 1: psf/requests
    selected_url = "https://github.com/psf/requests"
    api_key = None  # Skip API key for testing
    
    print(f"Starting analysis of: {selected_url}")
    print("This may take a few minutes depending on repository size...")
    
    try:
        # Initialize analyzer
        analyzer = GitHubCodeAnalyzer(workspace_dir="./demo-workspace")
        
        # Run analysis
        results = analyzer.analyze_repository(selected_url, api_key)
        
        # Show results
        print("\n" + "=" * 60)
        print("TEST RESULTS")
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
        
        print(f"\nTest completed!")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_option_1()