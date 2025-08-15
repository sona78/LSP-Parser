import asyncio
import json
import os
import sys
import signal
from multilspy import LanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from files import GRAPH_JSON_FILE, CALL_GRAPH_JSON_FILE, DECLARATION_GRAPH_JSON_FILE

# Store the original working directory
original_cwd = os.getcwd()
repository_root_path = os.path.abspath("demo-workspace/requests")

class TimeoutError(Exception):
    """Custom timeout exception for Windows compatibility."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Operation timed out")

async def build_code_graph_with_multilspy(repository_root_path, original_cwd):
    """Build code graph using multilspy with proper working directory handling."""
    
    print(f"Repository root path: {repository_root_path}")
    print(f"Original working directory: {original_cwd}")
    
    # Ensure we start from the original working directory where LSP tools are available
    os.chdir(original_cwd)
    
    config = MultilspyConfig.from_dict({"code_language": "python"})
    logger = MultilspyLogger()
    
    print("Creating language server...")
    lsp = LanguageServer.create(config, logger, repository_root_path)
    print(f"Language server created: {type(lsp).__name__}")
    
    print("Starting language server...")
    async with lsp.start_server():
        print("Language server started successfully!")
        
        # After LSP is started, we can work with the repository files
        # but keep the LSP server running from the original directory
        repo_files = []
        for root, dirs, files in os.walk(repository_root_path):
            for file in files:
                if file.endswith('.py'):
                    repo_files.append(os.path.join(root, file))
        
        print(f"Found Python files: {[os.path.basename(f) for f in repo_files[:10]]}")  # Show first 10
        
        # Rest of the processing logic would go here...
        # For this test, just verify the LSP server starts properly
        return True

async def main():
    """Main function with timeout."""
    try:
        result = await asyncio.wait_for(
            build_code_graph_with_multilspy(repository_root_path, original_cwd),
            timeout=60.0  # 1 minute timeout for testing
        )
        return result
    except asyncio.TimeoutError:
        print("Operation timed out")
        return False
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # For Windows compatibility - signal may not work
    if os.name != 'nt':
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(300)  # 5 minute timeout
    
    try:
        result = asyncio.run(main())
        if result:
            print("Test successful - LSP server started properly")
        else:
            print("Test failed")
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()