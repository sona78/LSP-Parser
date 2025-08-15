#!/usr/bin/env python3
"""
Debug LSP path configuration issues.
"""

import os
from pathlib import Path

def debug_lsp_paths():
    """Debug LSP path configurations."""
    print("=" * 60)
    print("LSP PATH DEBUG")
    print("=" * 60)
    
    # Test path from our setup
    repo_path = "demo-workspace/requests"
    abs_path = os.path.abspath(repo_path)
    
    print(f"Repository path: {repo_path}")
    print(f"Absolute path: {abs_path}")
    print(f"Path exists: {os.path.exists(abs_path)}")
    
    # Test the root_uri conversion
    root_uri = f"file:///{abs_path.replace(os.sep, '/')}"
    print(f"Root URI: {root_uri}")
    
    # Test different URI formats
    print("\nTesting different URI formats:")
    
    # Method 1: Simple forward slash replacement
    uri1 = f"file:///{abs_path.replace(os.sep, '/')}"
    print(f"Method 1: {uri1}")
    
    # Method 2: pathlib conversion
    uri2 = Path(abs_path).as_uri()
    print(f"Method 2: {uri2}")
    
    # Method 3: Windows-specific handling
    if os.name == 'nt':
        # On Windows, ensure proper file:// format
        uri3 = f"file:///{abs_path.replace(chr(92), '/')}"  # Replace backslash
        print(f"Method 3: {uri3}")
    
    # Test if the directory is readable
    print(f"\nDirectory tests:")
    print(f"Can list directory: {os.access(abs_path, os.R_OK)}")
    try:
        files = os.listdir(abs_path)
        print(f"Contains {len(files)} items")
        print(f"First few items: {files[:5]}")
    except Exception as e:
        print(f"Cannot list directory: {e}")
    
    # Test current working directory context
    print(f"\nWorking directory tests:")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Relative path exists: {os.path.exists(repo_path)}")

if __name__ == "__main__":
    debug_lsp_paths()