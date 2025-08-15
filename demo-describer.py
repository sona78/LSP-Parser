#!/usr/bin/env python3
"""
Demo script for the Code Graph Describer

This script demonstrates the key features of basic-describer.py
without requiring user input.
"""

import sys
import os

# Import the describer
exec(open('basic-describer.py').read())

def demo_basic_functionality():
    """Demonstrate basic functionality."""
    print("=" * 60)
    print("DEMO: Code Graph Describer")
    print("=" * 60)
    
    # Initialize describer
    print("\n1. Initializing Code Graph Describer...")
    describer = CodeGraphDescriber()
    
    # Show statistics
    print(f"\n2. Graph Statistics:")
    print(f"   - Total nodes: {len(describer.nodes)}")
    print(f"   - Total edges: {len(describer.edges)}")
    
    functions = describer.list_nodes('FUNCTION')
    classes = describer.list_nodes('CLASS')
    methods = describer.list_nodes('METHOD')
    
    print(f"   - Functions: {len(functions)}")
    print(f"   - Classes: {len(classes)}")
    print(f"   - Methods: {len(methods)}")
    
    # Show source extraction results
    nodes_with_source = [n for n in describer.nodes.values() if n.source_code]
    nodes_with_docstring = [n for n in describer.nodes.values() if n.docstring]
    
    print(f"   - Nodes with source code: {len(nodes_with_source)}")
    print(f"   - Nodes with docstrings: {len(nodes_with_docstring)}")
    
    # Demonstrate node context
    print(f"\n3. Sample Node Analysis:")
    
    # Find the Calculator class
    calc_class = None
    for node in describer.nodes.values():
        if node.name == 'Calculator' and node.kind == 'CLASS':
            calc_class = node
            break
    
    if calc_class:
        print(f"\n   Calculator Class:")
        print(f"   - Location: {calc_class.file}:{calc_class.line}")
        print(f"   - Dependencies: {len(calc_class.dependencies)}")
        print(f"   - Used by: {len(calc_class.dependents)}")
        
        if calc_class.source_code:
            lines = calc_class.source_code.split('\n')
            print(f"   - Source preview: {lines[0]}")
        
        if calc_class.docstring:
            print(f"   - Has docstring: Yes")
    
    # Show method example
    add_method = None
    for node in describer.nodes.values():
        if node.name == 'add' and node.kind == 'METHOD':
            add_method = node
            break
    
    if add_method:
        print(f"\n   Add Method:")
        print(f"   - Location: {add_method.file}:{add_method.line}")
        print(f"   - Dependencies: {len(add_method.dependencies)}")
        
        if add_method.docstring:
            docstring_preview = add_method.docstring[:100] + "..." if len(add_method.docstring) > 100 else add_method.docstring
            print(f"   - Docstring: {docstring_preview}")
    
    # Demonstrate context retrieval
    print(f"\n4. Context Analysis Example:")
    if calc_class:
        context = describer.get_node_context(calc_class.id)
        if context:
            print(f"   Calculator context retrieved successfully")
            print(f"   - File siblings: {len(context['file_siblings'])}")
            print(f"   - Dependencies: {[dep.name for dep in context['dependencies'][:3]]}")
            print(f"   - Dependents: {[dep.name for dep in context['dependents'][:3]]}")
    
    # Show Gemini integration readiness
    print(f"\n5. AI Integration Status:")
    if GEMINI_AVAILABLE:
        print("   - Gemini API package: Available")
        print("   - Ready for AI descriptions with API key")
    else:
        print("   - Gemini API package: Not installed")
        print("   - Install with: pip install google-generativeai")
    
    # Show available commands
    print(f"\n6. Interactive Features Available:")
    print("   - list [kind] [file] - List nodes")
    print("   - describe <node_id> - AI description (requires API key)")
    print("   - relations <node_id> - AI relationship analysis")
    print("   - context <node_id> - Show node context")
    print("   - search <name> - Search for nodes")
    print("   - files - List all files")
    
    print(f"\n7. Sample Node IDs for testing:")
    sample_nodes = list(describer.nodes.keys())[:5]
    for node_id in sample_nodes:
        node = describer.nodes[node_id]
        print(f"   - {node_id} ({node.kind})")
    
    print(f"\n8. To start interactive mode:")
    print("   python basic-describer.py")
    
    print("\n" + "=" * 60)
    print("Demo completed! The describer is ready for use.")
    print("=" * 60)

if __name__ == "__main__":
    demo_basic_functionality()