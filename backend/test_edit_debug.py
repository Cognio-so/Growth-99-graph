# test_edit_debug.py
"""
Debug script to test the editing flow step by step.
"""

def test_edit_flow_debug():
    """Test the editing flow with debug information."""
    
    print("🧪 Testing Edit Flow Debug...")
    
    # Step 1: Check if we can access the global sandbox
    try:
        from nodes.apply_to_Sandbox_node import _global_sandbox
        print(f"✅ Global sandbox accessible: {_global_sandbox is not None}")
        
        if _global_sandbox:
            print(f"   Sandbox ID: {getattr(_global_sandbox, 'id', 'unknown')}")
            
            # Try to read a file to test sandbox health
            try:
                test_result = _global_sandbox.commands.run("echo 'test'", timeout=5)
                if test_result and test_result.stdout:
                    print("   ✅ Sandbox is healthy and responding")
                else:
                    print("   ⚠️ Sandbox may not be healthy")
            except Exception as e:
                print(f"   ❌ Sandbox health check failed: {e}")
        else:
            print("   ⚠️ No global sandbox available")
            
    except ImportError as e:
        print(f"❌ Could not import sandbox: {e}")
    
    # Step 2: Test file capture
    try:
        from nodes.edit_analyzer_node import _capture_existing_code_context
        print("✅ Edit analyzer functions accessible")
        
        # Test context capture
        test_state = {"text": "test"}
        context = _capture_existing_code_context(test_state)
        print(f"   Context capture result: {len(context)} characters")
        print(f"   Context preview: {context[:100]}...")
        
    except Exception as e:
        print(f"❌ Edit analyzer test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_edit_flow_debug()
