#!/usr/bin/env python3
"""
Simple test for the parser without full GitHub analysis.
"""

import os
import sys
from pathlib import Path

# Import our analyzer
exec(open('basic-code-entry.py').read().replace('if __name__ == "__main__":', 'if False:'))

def test_parser_only():
    """Test just the parser on the already cloned repository."""
    print("=" * 60)
    print("TEST: Parser Only")
    print("=" * 60)
    
    repo_path = Path("demo-workspace/requests")
    
    if not repo_path.exists():
        print(f"Repository not found at {repo_path}")
        return False
    
    print(f"Testing parser on: {repo_path}")
    
    try:
        # Initialize analyzer
        analyzer = GitHubCodeAnalyzer(workspace_dir="./demo-workspace")
        
        # Test just the parsing step
        success = analyzer.run_parser(repo_path)
        
        if success:
            print("[OK] Parser completed successfully")
            
            # Check if artifacts were generated
            artifacts_dir = Path("artifacts")
            if artifacts_dir.exists():
                print(f"Generated artifacts:")
                for file in artifacts_dir.glob("*.json"):
                    print(f"  - {file.name}")
        else:
            print("[FAIL] Parser failed")
        
        return success
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_parser_only()