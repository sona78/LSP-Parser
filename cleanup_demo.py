#!/usr/bin/env python3
"""
Script to clean up demo workspace on Windows.
"""

import os
import shutil
import stat
from pathlib import Path

def remove_readonly(func, path, _):
    """Clear readonly bit and reattempt removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def cleanup_demo_workspace():
    """Clean up the demo workspace directory."""
    demo_dir = Path("demo-workspace")
    
    if demo_dir.exists():
        print(f"Removing {demo_dir}...")
        try:
            shutil.rmtree(demo_dir, onerror=remove_readonly)
            print("Demo workspace cleaned successfully!")
        except Exception as e:
            print(f"Error cleaning workspace: {e}")
    else:
        print("Demo workspace doesn't exist - nothing to clean")

if __name__ == "__main__":
    cleanup_demo_workspace()