# GitHub Repository Code Analysis System

This system provides end-to-end analysis of GitHub repositories using the complete Lynx parser pipeline.

## Features

🔗 **GitHub Integration**
- Clone any public GitHub repository
- Automatic repository validation
- Clean workspace management

🔍 **Code Analysis**
- Multilspy-based Python code parsing
- Extract functions, classes, methods, and relationships
- Generate comprehensive dependency graphs

📊 **Interactive Visualization**
- React-based graph visualization
- Navigate code relationships visually
- Export to multiple formats

🤖 **AI-Powered Descriptions**
- Gemini AI integration for code explanations
- Context-aware function and class descriptions
- Relationship analysis and architectural insights

## Quick Start

### Basic Usage (Interactive Mode)
```bash
python basic-code-entry.py
```

### Command Line Usage
```bash
# Analyze a repository
python basic-code-entry.py https://github.com/user/repository

# With AI features
python basic-code-entry.py https://github.com/user/repo --api-key YOUR_GEMINI_KEY

# Custom workspace
python basic-code-entry.py https://github.com/user/repo --workspace ./my-workspace
```

### Programmatic Usage
```python
from basic_code_entry import GitHubCodeAnalyzer

analyzer = GitHubCodeAnalyzer()
results = analyzer.analyze_repository(
    "https://github.com/user/repository",
    gemini_api_key="your-api-key"  # optional
)

print(f"Analysis completed: {results['stages']}")
print(f"Generated artifacts: {results['artifacts']}")
```

## Pipeline Stages

### 1. Repository Cloning
- Validates GitHub URL
- Performs shallow clone for efficiency
- Creates isolated workspace

### 2. Code Parsing
- Uses multilspy language server
- Extracts Python code structure
- Generates graph data (nodes and edges)
- Outputs to `react-graph-viewer/public/artifacts/`

### 3. Visualization Building
- Builds React application
- Processes graph data for interactive display
- Generates standalone HTML visualization

### 4. AI Description Setup
- Initializes code describer
- Prepares for AI-powered analysis
- Enables interactive exploration

## Generated Outputs

After successful analysis, you'll have:

```
workspace/
├── [repository-name]/           # Cloned repository
react-graph-viewer/
├── public/artifacts/
│   ├── combined_graph.json      # Full graph data
│   ├── call_graph.json          # Function call relationships
│   └── declaration_graph.json   # Class/method structure
└── build/
    └── index.html               # Interactive visualization
```

## Next Steps After Analysis

1. **Explore with AI Describer**
   ```bash
   python basic-describer.py
   
   # Interactive commands:
   > list                        # Show all nodes
   > describe Calculator::main.py # AI description
   > relations add::operations.py # Relationship analysis
   ```

2. **View Interactive Visualization**
   - Open `react-graph-viewer/build/index.html` in browser
   - Navigate the code graph visually
   - Switch between different graph views

3. **Analyze Specific Components**
   ```bash
   # Use describer commands
   > context Calculator::main.py  # Show context
   > search "validate"           # Find nodes by name
   > files                       # List all analyzed files
   ```

## Requirements

- Python 3.8+
- Git (for repository cloning)
- Node.js & npm (for React visualization)
- Dependencies:
  - multilspy
  - google-generativeai (optional, for AI features)

## Error Handling

The system gracefully handles:
- Invalid GitHub URLs
- Repositories without Python code
- Network connectivity issues
- Missing dependencies
- Parser failures

Each stage reports success/failure independently, allowing partial analysis even if some stages fail.

## Example Analysis Flow

```bash
$ python basic-code-entry.py https://github.com/example/python-project

============================================================
GITHUB REPOSITORY ANALYSIS
============================================================
Repository: example/python-project
URL: https://github.com/example/python-project

1. Cloning repository...
Successfully cloned repository to workspace/python-project
✓ Repository cloned successfully

2. Parsing code structure...
Found 15 Python files to analyze
Language server started successfully!
Parser completed successfully
✓ Code parsing completed

3. Building visualization...
Installing npm dependencies...
Building React app...
✓ Visualization built successfully

4. Setting up AI describer...
Code describer ready!
✓ AI describer ready

============================================================
ANALYSIS COMPLETE
============================================================
Completed 4/4 stages successfully

Generated artifacts:
  - combined_graph: 45 nodes, 67 edges
  - call_graph: 45 nodes, 23 edges
  - declaration_graph: 45 nodes, 44 edges

Next steps:
  1. Run: python basic-describer.py
  2. Use 'extract' command to get detailed info
  3. Use 'describe <node_id>' for AI descriptions
  4. Open react-graph-viewer/build/index.html for visualization
```

## Troubleshooting

**Repository cloning fails:**
- Check internet connection
- Verify GitHub URL is correct and public
- Ensure Git is installed

**Parser fails:**
- Ensure repository contains Python files
- Check for syntax errors in Python code
- Verify multilspy dependencies are installed

**React build fails:**
- Ensure Node.js and npm are installed
- Check npm dependencies in react-graph-viewer/
- Try `npm install` manually in react-graph-viewer/

**AI features unavailable:**
- Install: `pip install google-generativeai`
- Obtain Gemini API key from Google AI Studio
- Set as environment variable: `export GEMINI_API_KEY=your-key`