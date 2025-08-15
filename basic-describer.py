#!/usr/bin/env python3
"""
Code Graph Describer with Gemini AI Integration

This module loads graph data from JSON artifacts and provides AI-powered
descriptions of code nodes and their relationships using Google's Gemini API.

Features:
- Load graph data from JSON files
- Extract source code for any node
- Generate AI descriptions using Gemini API
- Analyze node relationships and dependencies
- Interactive CLI for exploring the codebase
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

# Import parser functionality
PARSER_AVAILABLE = False
run_parser_on_directory = None
setup_lsp = None
get_parser_config = None
find_python_files = None

def _import_parser_functions():
    """Import parser functions dynamically to avoid circular imports."""
    global PARSER_AVAILABLE, run_parser_on_directory, setup_lsp, get_parser_config, find_python_files
    
    if PARSER_AVAILABLE:
        return  # Already imported
    
    try:
        # Try importing as module
        import importlib.util
        spec = importlib.util.spec_from_file_location("basic_parser", "basic-parser.py")
        if spec and spec.loader:
            basic_parser = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(basic_parser)
            
            run_parser_on_directory = basic_parser.run_parser_on_directory
            setup_lsp = basic_parser.setup_lsp
            get_parser_config = basic_parser.get_parser_config
            find_python_files = basic_parser.find_python_files
            PARSER_AVAILABLE = True
            return
    except Exception:
        pass
    
    try:
        # Fallback: read and exec with guards
        with open('basic-parser.py', 'r') as f:
            parser_code = f.read()
        
        # Create a separate namespace to avoid conflicts
        parser_globals = {}
        parser_locals = {}
        
        # Remove the main execution
        parser_code = parser_code.replace('if __name__ == "__main__":', 'if False:')
        
        exec(parser_code, parser_globals, parser_locals)
        
        run_parser_on_directory = parser_locals.get('run_parser_on_directory')
        setup_lsp = parser_locals.get('setup_lsp') 
        get_parser_config = parser_locals.get('get_parser_config')
        find_python_files = parser_locals.get('find_python_files')
        
        if all([run_parser_on_directory, setup_lsp, get_parser_config, find_python_files]):
            PARSER_AVAILABLE = True
        else:
            print("Warning: Could not find all required parser functions")
            
    except Exception as e:
        print(f"Warning: Could not import basic-parser functionality: {e}")
        PARSER_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False
    print("Note: google-generativeai not installed. AI features will be disabled.")


@dataclass
class NodeInfo:
    """Enhanced node information with source code and context from language server."""
    id: str
    name: str
    kind: str
    file: str
    line: int
    source_code: Optional[str] = None
    docstring: Optional[str] = None
    symbol_info: Optional[Dict] = None  # Raw symbol info from language server
    hover_info: Optional[str] = None    # Hover information from language server
    definition_info: Optional[Dict] = None  # Definition details
    dependencies: List[str] = None
    dependents: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.dependents is None:
            self.dependents = []


class CodeGraphDescriber:
    """Main class for analyzing code graphs with AI descriptions."""
    
    def __init__(self, artifacts_path: str = "./react-graph-viewer/public/artifacts", 
                 repository_path: str = "./test-project",
                 auto_parse: bool = True):
        """
        Initialize the code graph describer.
        
        Args:
            artifacts_path: Path to JSON graph files
            repository_path: Path to source code repository
            auto_parse: Whether to automatically run parser if artifacts don't exist
        """
        self.artifacts_path = Path(artifacts_path)
        self.repository_path = Path(repository_path)
        self.nodes: Dict[str, NodeInfo] = {}
        self.edges: List[Dict[str, str]] = []
        self.lsp = None
        self.gemini_model = None
        
        # Check if artifacts exist, if not and auto_parse is True, run parser
        if auto_parse and not self._artifacts_exist():
            self._run_parser_to_generate_artifacts()
        
        # Load graph data
        self._load_graph_data()
        self._setup_language_server()
        self._extract_source_code_simple()
        self._build_dependency_graph()
    
    def _artifacts_exist(self) -> bool:
        """Check if the required artifact files exist."""
        required_files = ["combined_graph.json", "call_graph.json", "declaration_graph.json"]
        return all((self.artifacts_path / file).exists() for file in required_files)
    
    def _run_parser_to_generate_artifacts(self):
        """Run the basic parser to generate graph artifacts."""
        _import_parser_functions()
        
        if not PARSER_AVAILABLE or not run_parser_on_directory:
            print("Warning: Parser not available. Cannot generate artifacts automatically.")
            return False
            
        print(f"Artifacts not found. Running parser on {self.repository_path}...")
        
        try:
            success = run_parser_on_directory(str(self.repository_path))
            if success:
                print("Parser completed successfully!")
                return True
            else:
                print("Parser failed to generate artifacts.")
                return False
        except Exception as e:
            print(f"Error running parser: {e}")
            return False
        
    def setup_gemini_api(self, api_key: str = None):
        """
        Set up Gemini API for AI descriptions.
        
        Args:
            api_key: Gemini API key. If None, looks for GEMINI_API_KEY environment variable
        """
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
            
        if not api_key:
            print("Warning: No Gemini API key found. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
            print("AI descriptions will not be available.")
            return False
            
        try:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            print("Gemini AI successfully initialized!")
            return True
        except Exception as e:
            print(f"Error initializing Gemini AI: {e}")
            return False
            
    def _load_graph_data(self):
        """Load graph data from JSON files."""
        combined_path = self.artifacts_path / "combined_graph.json"
        
        if not combined_path.exists():
            raise FileNotFoundError(f"Graph data not found at {combined_path}")
            
        with open(combined_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
            
        # Load nodes
        for node_data in graph_data.get('nodes', []):
            node = NodeInfo(
                id=node_data['id'],
                name=node_data['name'],
                kind=node_data['kind'],
                file=node_data['file'],
                line=node_data['line']
            )
            self.nodes[node.id] = node
            
        # Load edges
        self.edges = graph_data.get('edges', [])
        
        print(f"Loaded {len(self.nodes)} nodes and {len(self.edges)} edges")
        
    def _setup_language_server(self):
        """Set up the language server for enhanced code analysis."""
        _import_parser_functions()
        
        if not PARSER_AVAILABLE or not setup_lsp:
            print("Warning: Parser not available. Language server features disabled.")
            return
            
        try:
            # Use the parser's LSP setup function
            abs_repo_path = os.path.abspath(self.repository_path)
            self.lsp = setup_lsp(abs_repo_path)
            print("Language server initialized successfully using parser setup")
        except Exception as e:
            print(f"Warning: Could not initialize language server: {e}")
            print("Some advanced features may not be available")
            
    def _extract_source_code_simple(self):
        """Extract source code using simple file reading and line-based extraction."""
        print("Extracting source code using simple file reading...")
        
        for node in self.nodes.values():
            try:
                abs_repo_path = os.path.abspath(self.repository_path)
                file_path = os.path.join(abs_repo_path, node.file)
                
                if not os.path.exists(file_path):
                    continue
                    
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Simple extraction based on line number and basic heuristics
                start_line = max(0, node.line - 1)  # Convert to 0-based
                
                # Try to find the end of the definition
                end_line = start_line + 1
                if start_line < len(lines):
                    current_line = lines[start_line].strip()
                    
                    # Determine extraction strategy based on node kind
                    if node.kind in ['FUNCTION', 'METHOD']:
                        # Look for function definition and extract until next function/class or end of indentation
                        end_line = self._find_function_end(lines, start_line)
                    elif node.kind == 'CLASS':
                        # Extract class definition and its content
                        end_line = self._find_class_end(lines, start_line)
                    else:
                        # For other types, just take a few lines
                        end_line = min(start_line + 3, len(lines))
                    
                    # Extract the source code
                    source_lines = lines[start_line:end_line]
                    node.source_code = ''.join(source_lines).rstrip()
                    
                    # Try to extract docstring
                    if node.kind in ['FUNCTION', 'METHOD', 'CLASS']:
                        node.docstring = self._extract_docstring_simple(lines, start_line)
                        
            except Exception as e:
                print(f"Warning: Could not extract source for {node.name}: {e}")
                
        nodes_with_source = len([n for n in self.nodes.values() if n.source_code])
        print(f"Extracted source code for {nodes_with_source} nodes")
        
    def _find_function_end(self, lines: List[str], start_line: int) -> int:
        """Find the end line of a function definition."""
        if start_line >= len(lines):
            return start_line + 1
            
        # Get the indentation of the function definition
        func_line = lines[start_line]
        base_indent = len(func_line) - len(func_line.lstrip())
        
        i = start_line + 1
        while i < len(lines):
            line = lines[i]
            if line.strip() == '':
                i += 1
                continue
                
            current_indent = len(line) - len(line.lstrip())
            
            # If we hit a line with same or less indentation that's not empty, we're done
            if current_indent <= base_indent and line.strip():
                break
                
            i += 1
            
        return i
        
    def _find_class_end(self, lines: List[str], start_line: int) -> int:
        """Find the end line of a class definition."""
        if start_line >= len(lines):
            return start_line + 1
            
        # Get the indentation of the class definition
        class_line = lines[start_line]
        base_indent = len(class_line) - len(class_line.lstrip())
        
        i = start_line + 1
        while i < len(lines):
            line = lines[i]
            if line.strip() == '':
                i += 1
                continue
                
            current_indent = len(line) - len(line.lstrip())
            
            # If we hit a line with same or less indentation, we're done
            if current_indent <= base_indent and line.strip():
                break
                
            i += 1
            
        return i
        
    def _extract_docstring_simple(self, lines: List[str], start_line: int) -> Optional[str]:
        """Extract docstring from function/class definition."""
        try:
            # Look for docstring in the next few lines after definition
            for i in range(start_line + 1, min(start_line + 5, len(lines))):
                line = lines[i].strip()
                if line.startswith('"""') or line.startswith("'''"):
                    # Found start of docstring
                    quote_type = '"""' if line.startswith('"""') else "'''"
                    
                    # Check if it's a single-line docstring
                    if line.count(quote_type) == 2:
                        return line.replace(quote_type, '').strip()
                    
                    # Multi-line docstring
                    docstring_lines = [line.replace(quote_type, '')]
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if quote_type in next_line:
                            docstring_lines.append(next_line.replace(quote_type, ''))
                            break
                        docstring_lines.append(next_line)
                    
                    return '\n'.join(docstring_lines).strip()
                    
        except Exception:
            pass
            
        return None
            
    async def _extract_node_details_async(self):
        """Extract detailed information for all nodes using the language server."""
        if not self.lsp:
            print("Language server not available, skipping detailed extraction")
            return
            
        print("Extracting detailed node information using language server...")
        
        async with self.lsp.start_server():
            for node in self.nodes.values():
                try:
                    await self._extract_single_node_details(node)
                except Exception as e:
                    print(f"Warning: Could not extract details for {node.name}: {e}")
                    
        print("Finished extracting node details")
        
    async def _extract_single_node_details(self, node: NodeInfo):
        """Extract details for a single node using language server."""
        relative_path = node.file
        
        # Get hover information
        try:
            with self.lsp.open_file(relative_path):
                # Convert to 0-based line number for LSP
                line = node.line - 1
                char = 0
                
                # Get hover information
                hover_result = await self.lsp.request_hover(relative_path, line, char)
                if hover_result:
                    node.hover_info = hover_result.get('contents', '')
                
                # Get definition information  
                definition_result = await self.lsp.request_definition(relative_path, line, char)
                if definition_result:
                    node.definition_info = definition_result
                    
                # Get document symbols to find the exact symbol
                symbols, _ = await self.lsp.request_document_symbols(relative_path)
                if symbols:
                    matching_symbol = self._find_matching_symbol(symbols, node)
                    if matching_symbol:
                        node.symbol_info = matching_symbol
                        # Extract source code from symbol range
                        node.source_code = await self._extract_source_from_symbol(
                            relative_path, matching_symbol)
                        
        except Exception as e:
            print(f"Error extracting details for {node.name}: {e}")
            
    def _find_matching_symbol(self, symbols: List[Dict], node: NodeInfo) -> Optional[Dict]:
        """Find the symbol that matches our node."""
        def search_symbols(symbol_list):
            for symbol in symbol_list:
                if symbol.get('name') == node.name:
                    symbol_line = symbol.get('range', {}).get('start', {}).get('line', 0) + 1
                    if abs(symbol_line - node.line) <= 2:  # Allow some tolerance
                        return symbol
                # Search in children
                if 'children' in symbol:
                    result = search_symbols(symbol['children'])
                    if result:
                        return result
            return None
            
        return search_symbols(symbols)
        
    async def _extract_source_from_symbol(self, file_path: str, symbol: Dict) -> Optional[str]:
        """Extract source code from symbol range information."""
        try:
            # Read the file
            abs_repo_path = os.path.abspath(self.repository_path)
            full_path = os.path.join(abs_repo_path, file_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Extract range
            range_info = symbol.get('range', {})
            start_line = range_info.get('start', {}).get('line', 0)
            end_line = range_info.get('end', {}).get('line', start_line)
            
            # Extract source code
            source_lines = lines[start_line:end_line + 1]
            return ''.join(source_lines).rstrip()
            
        except Exception as e:
            print(f"Error extracting source code: {e}")
            return None
        
    def _build_dependency_graph(self):
        """Build dependency relationships between nodes."""
        # Create dependency mappings
        for edge in self.edges:
            source_id = edge['from']
            target_id = edge['to']
            
            if source_id in self.nodes and target_id in self.nodes:
                # source depends on target (source calls/uses target)
                self.nodes[source_id].dependencies.append(target_id)
                # target is used by source
                self.nodes[target_id].dependents.append(source_id)
                
    def extract_detailed_info(self):
        """
        Extract detailed information for all nodes using the language server.
        This is a synchronous wrapper for the async method.
        """
        if not self.lsp:
            print("Language server not available")
            return
            
        print("Starting detailed information extraction...")
        asyncio.run(self._extract_node_details_async())
        
    def get_node_context(self, node_id: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a node including dependencies and source code.
        
        Args:
            node_id: The node identifier
            
        Returns:
            Dictionary with node context information
        """
        if node_id not in self.nodes:
            return None
            
        node = self.nodes[node_id]
        
        # Get dependency nodes
        dependency_nodes = [self.nodes[dep_id] for dep_id in node.dependencies if dep_id in self.nodes]
        dependent_nodes = [self.nodes[dep_id] for dep_id in node.dependents if dep_id in self.nodes]
        
        # Get file context (other nodes in the same file)
        file_nodes = [n for n in self.nodes.values() if n.file == node.file and n.id != node_id]
        
        return {
            'node': node,
            'source_code': node.source_code,
            'docstring': node.docstring,
            'hover_info': node.hover_info,
            'symbol_info': node.symbol_info,
            'definition_info': node.definition_info,
            'dependencies': dependency_nodes,
            'dependents': dependent_nodes,
            'file_siblings': file_nodes,
        }
        
    def describe_node_with_ai(self, node_id: str, include_context: bool = True) -> Optional[str]:
        """
        Generate an AI description of a node using Gemini.
        
        Args:
            node_id: The node identifier
            include_context: Whether to include dependency context
            
        Returns:
            AI-generated description or None if unavailable
        """
        if not self.gemini_model:
            print("Gemini AI not initialized. Call setup_gemini_api() first.")
            return None
            
        context = self.get_node_context(node_id)
        if not context:
            return None
            
        node = context['node']
        
        # Build prompt
        prompt_parts = [
            f"Analyze this {node.kind.lower()} from a Python codebase:\n",
            f"Name: {node.name}",
            f"File: {node.file}",
            f"Line: {node.line}",
            f"Type: {node.kind}\n"
        ]
        
        if context['source_code']:
            prompt_parts.append(f"Source Code:\n```python\n{context['source_code']}\n```\n")
            
        if context['hover_info']:
            prompt_parts.append(f"Language Server Info: {context['hover_info']}\n")
            
        if context['docstring']:
            prompt_parts.append(f"Documentation: {context['docstring']}\n")
            
        if include_context:
            if context['dependencies']:
                deps = [f"- {dep.name} ({dep.kind})" for dep in context['dependencies']]
                prompt_parts.append(f"Dependencies (what this uses):\n" + "\n".join(deps) + "\n")
                
            if context['dependents']:
                deps = [f"- {dep.name} ({dep.kind})" for dep in context['dependents']]
                prompt_parts.append(f"Used by:\n" + "\n".join(deps) + "\n")
                
        prompt_parts.append(
            "Please provide a comprehensive description including:\n"
            "1. Purpose and functionality\n"
            "2. Key parameters/inputs (if applicable)\n"
            "3. Return values/outputs (if applicable)\n" 
            "4. Role in the overall system\n"
            "5. Any notable implementation details\n"
        )
        
        prompt = "\n".join(prompt_parts)
        
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating AI description: {e}")
            return None
            
    def describe_node_relationships(self, node_id: str) -> Optional[str]:
        """
        Generate an AI description of a node's relationships and interactions.
        
        Args:
            node_id: The node identifier
            
        Returns:
            AI-generated relationship description
        """
        if not self.gemini_model:
            print("Gemini AI not initialized. Call setup_gemini_api() first.")
            return None
            
        context = self.get_node_context(node_id)
        if not context:
            return None
            
        node = context['node']
        
        prompt_parts = [
            f"Analyze the relationships and interactions for this {node.kind.lower()}: {node.name}\n",
        ]
        
        if context['dependencies']:
            prompt_parts.append("This component depends on/uses:")
            for dep in context['dependencies']:
                dep_context = self.get_node_context(dep.id)
                prompt_parts.append(f"- {dep.name} ({dep.kind}) in {dep.file}")
                if dep_context and dep_context['source_code']:
                    # Include snippet of dependency source
                    snippet = dep_context['source_code'][:200] + "..." if len(dep_context['source_code']) > 200 else dep_context['source_code']
                    prompt_parts.append(f"  Code: {snippet}")
            prompt_parts.append("")
            
        if context['dependents']:
            prompt_parts.append("This component is used by:")
            for dep in context['dependents']:
                prompt_parts.append(f"- {dep.name} ({dep.kind}) in {dep.file}")
            prompt_parts.append("")
            
        prompt_parts.append(
            "Please analyze and describe:\n"
            "1. How this component interacts with its dependencies\n"
            "2. What role it plays for the components that use it\n"
            "3. The data flow and control flow patterns\n"
            "4. Any design patterns or architectural relationships\n"
            "5. Potential impact if this component were modified\n"
        )
        
        prompt = "\n".join(prompt_parts)
        
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating relationship description: {e}")
            return None
            
    def list_nodes(self, kind_filter: str = None, file_filter: str = None) -> List[NodeInfo]:
        """
        List nodes with optional filtering.
        
        Args:
            kind_filter: Filter by node kind (e.g., 'FUNCTION', 'CLASS', 'METHOD')
            file_filter: Filter by filename
            
        Returns:
            List of matching nodes
        """
        nodes = list(self.nodes.values())
        
        if kind_filter:
            nodes = [n for n in nodes if n.kind == kind_filter.upper()]
            
        if file_filter:
            nodes = [n for n in nodes if file_filter in n.file]
            
        return sorted(nodes, key=lambda n: (n.file, n.line))
        
    def interactive_explore(self):
        """Interactive CLI for exploring the codebase."""
        print("\n=== Code Graph Explorer ===")
        print("Commands:")
        print("  list [kind] [file] - List nodes (optionally filtered)")
        print("  parse - Run parser to regenerate graph data")
        print("  extract - Extract detailed info using language server")
        print("  describe <node_id> - Get AI description of a node")
        print("  relations <node_id> - Get AI description of node relationships") 
        print("  context <node_id> - Show node context without AI")
        print("  hover <node_id> - Show language server hover info")
        print("  search <name> - Search for nodes by name")
        print("  files - List all files")
        print("  quit - Exit")
        
        while True:
            try:
                command = input("\n> ").strip().split()
                if not command:
                    continue
                    
                cmd = command[0].lower()
                
                if cmd == 'quit':
                    break
                    
                elif cmd == 'list':
                    kind_filter = command[1] if len(command) > 1 else None
                    file_filter = command[2] if len(command) > 2 else None
                    nodes = self.list_nodes(kind_filter, file_filter)
                    
                    for node in nodes[:20]:  # Limit output
                        print(f"  {node.id} - {node.name} ({node.kind}) - {node.file}:{node.line}")
                    if len(nodes) > 20:
                        print(f"  ... and {len(nodes) - 20} more nodes")
                        
                elif cmd == 'extract':
                    print("Extracting detailed information using language server...")
                    self.extract_detailed_info()
                    print("Extraction complete!")
                    
                elif cmd == 'parse':
                    print("Running parser to regenerate graph data...")
                    if self._run_parser_to_generate_artifacts():
                        print("Re-loading graph data...")
                        self._load_graph_data()
                        self._extract_source_code_simple()
                        self._build_dependency_graph()
                        print("Parser and reload complete!")
                    else:
                        print("Parser failed.")
                        
                elif cmd == 'describe':
                    if len(command) < 2:
                        print("Usage: describe <node_id>")
                        continue
                    node_id = command[1]
                    description = self.describe_node_with_ai(node_id)
                    if description:
                        print(f"\nAI Description of {node_id}:")
                        print("=" * 50)
                        print(description)
                    else:
                        print("Could not generate description.")
                        
                elif cmd == 'relations':
                    if len(command) < 2:
                        print("Usage: relations <node_id>")
                        continue
                    node_id = command[1]
                    description = self.describe_node_relationships(node_id)
                    if description:
                        print(f"\nAI Relationship Analysis of {node_id}:")
                        print("=" * 50)
                        print(description)
                    else:
                        print("Could not generate relationship analysis.")
                        
                elif cmd == 'context':
                    if len(command) < 2:
                        print("Usage: context <node_id>")
                        continue
                    node_id = command[1]
                    context = self.get_node_context(node_id)
                    if context:
                        node = context['node']
                        print(f"\nContext for {node.name}:")
                        print(f"  Type: {node.kind}")
                        print(f"  File: {node.file}:{node.line}")
                        if context['source_code']:
                            print(f"  Source:\n{context['source_code']}")
                        if context['hover_info']:
                            print(f"  Language Server Info: {context['hover_info']}")
                        if context['dependencies']:
                            print(f"  Dependencies: {[n.name for n in context['dependencies']]}")
                        if context['dependents']:
                            print(f"  Used by: {[n.name for n in context['dependents']]}")
                    else:
                        print("Node not found.")
                        
                elif cmd == 'hover':
                    if len(command) < 2:
                        print("Usage: hover <node_id>")
                        continue
                    node_id = command[1]
                    if node_id in self.nodes:
                        node = self.nodes[node_id]
                        print(f"\nLanguage Server Information for {node.name}:")
                        if node.hover_info:
                            print(f"Hover: {node.hover_info}")
                        if node.symbol_info:
                            print(f"Symbol Info: {node.symbol_info}")
                        if not node.hover_info and not node.symbol_info:
                            print("No language server info available. Run 'extract' first.")
                    else:
                        print("Node not found.")
                        
                elif cmd == 'search':
                    if len(command) < 2:
                        print("Usage: search <name>")
                        continue
                    search_term = command[1].lower()
                    matches = [n for n in self.nodes.values() if search_term in n.name.lower()]
                    for node in matches[:10]:
                        print(f"  {node.id} - {node.name} ({node.kind}) - {node.file}:{node.line}")
                        
                elif cmd == 'files':
                    files = set(n.file for n in self.nodes.values())
                    for file in sorted(files):
                        count = len([n for n in self.nodes.values() if n.file == file])
                        print(f"  {file} ({count} nodes)")
                        
                else:
                    print("Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                
        print("Goodbye!")


def main():
    """Main entry point."""
    print("Initializing Code Graph Describer...")
    
    # Check if we should specify a different repository
    import sys
    if len(sys.argv) > 1:
        repository_path = sys.argv[1]
        print(f"Using repository path: {repository_path}")
    else:
        repository_path = "./test-project"
    
    try:
        # Initialize with auto-parsing enabled
        describer = CodeGraphDescriber(repository_path=repository_path, auto_parse=True)
        
        # Setup Gemini API
        api_key = input("Enter Gemini API key (or press Enter to skip AI features): ").strip()
        if api_key:
            describer.setup_gemini_api(api_key)
        else:
            print("Skipping AI setup. You can still explore the graph structure.")
            
        # Start interactive mode
        describer.interactive_explore()
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure the repository path exists and contains Python files.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        

if __name__ == "__main__":
    main()