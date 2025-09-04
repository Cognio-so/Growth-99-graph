# test_editing_flow.py
"""
Test script to verify the editing flow works correctly.
This simulates a user making an edit request.
"""

import asyncio
from main import app
from fastapi.testclient import TestClient

def test_edit_flow():
    """Test the complete editing flow."""
    client = TestClient(app)
    
    # Test 1: Initial design generation
    print("🧪 Test 1: Initial design generation...")
    response1 = client.post("/api/query", data={
        "text": "Create a simple todo app with a blue theme",
        "llm_model": "groq-default"
    })
    
    if response1.status_code == 200:
        print("✅ Initial design generated successfully")
        session_id = response1.json()["session_id"]
        
        # Test 2: Edit request
        print("🧪 Test 2: Edit request...")
        response2 = client.post("/api/query", data={
            "text": "Change the button color from blue to red and add a new input field for priority",
            "llm_model": "groq-default",
            "session_id": session_id
        })
        
        if response2.status_code == 200:
            print("✅ Edit request processed successfully")
            result = response2.json()
            print(f"   Session ID: {result['session_id']}")
            print(f"   State keys: {list(result['state'].keys())}")
            
            # Check if edit analysis was performed
            context = result['state'].get('context', {})
            if 'edit_analysis' in context:
                edit_analysis = context['edit_analysis']
                print(f"   Edit type: {edit_analysis.get('edit_type')}")
                print(f"   Target files: {edit_analysis.get('target_files')}")
                print(f"   Changes: {edit_analysis.get('changes_description')}")
            else:
                print("   ⚠️ No edit analysis found in context")
        else:
            print(f"❌ Edit request failed: {response2.status_code}")
            print(f"   Error: {response2.text}")
    else:
        print(f"❌ Initial design failed: {response1.status_code}")
        print(f"   Error: {response1.text}")

if __name__ == "__main__":
    test_edit_flow()
