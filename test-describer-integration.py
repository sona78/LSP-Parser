#!/usr/bin/env python3
"""
Test script for the integrated describer functionality.
"""

# Import describer functionality
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

exec(open('basic-describer.py').read().replace('if __name__ == "__main__":', 'if False:'))

def test_integration():
    """Test the integration between describer and parser."""
    print("=" * 60)
    print("TESTING DESCRIBER INTEGRATION")
    print("=" * 60)
    
    try:
        # Initialize describer with auto_parse disabled since artifacts exist
        print("1. Initializing describer...")
        describer = CodeGraphDescriber(auto_parse=False)
        
        print(f"2. Loaded {len(describer.nodes)} nodes and {len(describer.edges)} edges")
        
        # Test listing nodes
        print("3. Testing node listing...")
        nodes = describer.list_nodes()
        print(f"   Found {len(nodes)} total nodes")
        
        if nodes:
            print("   First few nodes:")
            for node in nodes[:5]:
                print(f"     - {node.id}: {node.name} ({node.kind}) in {node.file}")
        
        # Test the parse command
        print("4. Testing parser integration...")
        result = describer._run_parser_to_generate_artifacts()
        print(f"   Parser execution result: {result}")
        
        # Test basic functionality
        print("5. Testing basic functionality...")
        functions = describer.list_nodes(kind_filter="FUNCTION")
        classes = describer.list_nodes(kind_filter="CLASS")
        print(f"   Functions: {len(functions)}")
        print(f"   Classes: {len(classes)}")
        
        print("\n" + "=" * 60)
        print("INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_integration()