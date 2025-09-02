# test_tracing.py - Run this to test if LangSmith tracing is working
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"

print("🔍 Checking LangSmith configuration...")
print(f"LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
print(f"LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT', 'default')}")
print(f"LANGCHAIN_API_KEY: {'✅ Set' if os.getenv('LANGCHAIN_API_KEY') else '❌ Not set'}")

# Test connection
try:
    from langsmith import Client
    client = Client()
    print("✅ Successfully connected to LangSmith!")
    
    # List recent runs (if any)
    runs = list(client.list_runs(limit=5))
    print(f"\n📊 Found {len(runs)} recent runs in your project")
    
except Exception as e:
    print(f"❌ Error connecting to LangSmith: {e}")
    print("\nPlease ensure:")
    print("1. You have set LANGCHAIN_API_KEY in your .env file")
    print("2. You have an account at https://smith.langchain.com")
    print("3. Your API key is valid")

# Test a simple traced function
if os.getenv('LANGCHAIN_API_KEY'):
    print("\n🧪 Running a test trace...")
    from langsmith import traceable
    
    @traceable(name="test_function", run_type="chain")
    def test_trace():
        return {"message": "Hello from traced function!"}
    
    result = test_trace()
    print("✅ Test trace completed!")
    print("Check https://smith.langchain.com to see if the trace appears")