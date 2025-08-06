import asyncio
import os
from multilspy import LanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

async def test_multilspy():
    # Configure multilspy
    config = MultilspyConfig(code_language="python")
    repository_root_path = os.path.abspath("test-project")
    config.root_uri = f"file:///{repository_root_path.replace(os.sep, '/')}"
    config.language_id = "python"
    
    # Create logger
    logger = MultilspyLogger()
    
    # Initialize language server
    language_server = LanguageServer.create(config, logger, repository_root_path)
    
    # Start server and make requests
    async with language_server.start_server():
        print("Language server started!")
        
        # Get references for Calculator import
        refs = await language_server.request_references("main.py", 7, 20)
        print(f"References: {refs}")
        
        # Get definition for Calculator
        definition = await language_server.request_definition("main.py", 7, 20)
        print(f"Definition: {definition}")

# Run the async function
asyncio.run(test_multilspy())