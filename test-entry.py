#!/usr/bin/env python3
"""Test script for basic-code-entry.py functionality."""

import sys
import os

# Read and execute the entry script without running main
with open('basic-code-entry.py', 'r') as f:
    content = f.read()

# Remove the main execution part
lines = content.split('\n')
filtered_lines = []
skip_main = False

for line in lines:
    if line.strip() == 'if __name__ == "__main__":':
        skip_main = True
    if not skip_main:
        filtered_lines.append(line)

exec('\n'.join(filtered_lines))

# Now test the functionality
print("Testing GitHubCodeAnalyzer...")

try:
    analyzer = GitHubCodeAnalyzer()
    print("Dependencies validated successfully")
    
    # Test repo info extraction
    test_urls = [
        'https://github.com/user/example-repo',
        'https://github.com/python/cpython.git',
        'https://github.com/microsoft/vscode'
    ]
    
    for url in test_urls:
        repo_info = analyzer.get_repo_info(url)
        print(f"OK: {url} -> {repo_info['full_name']}")
    
    print("\nGitHubCodeAnalyzer is ready!")
    print("\nTo use:")
    print("  python basic-code-entry.py")
    print("  python basic-code-entry.py https://github.com/user/repo")
    print("  python basic-code-entry.py https://github.com/user/repo --api-key YOUR_KEY")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)