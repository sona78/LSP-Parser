#!/usr/bin/env python3
"""
Debug script to check paths.
"""

import os
from pathlib import Path

def debug_paths():
    """Debug path configurations."""
    print("=" * 60)
    print("PATH DEBUG")
    print("=" * 60)
    
    current_dir = Path.cwd()
    print(f"Current working directory: {current_dir}")
    
    repo_dir = Path("demo-workspace/requests")
    print(f"Repository directory exists: {repo_dir.exists()}")
    print(f"Repository absolute path: {repo_dir.absolute()}")
    
    # Check basic-parser.py path replacement
    original_path = 'repository_root_path = os.path.abspath("test-project")'
    new_path = f'repository_root_path = os.path.abspath("{repo_dir}")'
    
    print(f"Original path string: {original_path}")
    print(f"New path string: {new_path}")
    
    # Test the actual path resolution
    test_path = os.path.abspath(str(repo_dir))
    print(f"os.path.abspath result: {test_path}")
    print(f"Path exists: {os.path.exists(test_path)}")
    
    # Check for any problematic characters
    has_backslashes = '\\' in str(test_path)
    print(f"Path contains backslashes: {has_backslashes}")
    print(f"Raw path: {repr(str(test_path))}")

if __name__ == "__main__":
    debug_paths()