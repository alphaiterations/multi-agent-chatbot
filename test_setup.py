"""
Test script for Text2SQL Chatbot
Run this to verify your setup is working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_dependencies():
    """Check if all required packages are installed"""
    print("Checking dependencies...")
    required_packages = {
        'langgraph': 'LangGraph',
        'openai': 'OpenAI',
        'chainlit': 'Chainlit',
        'pandas': 'Pandas',
        'sqlite3': 'SQLite3'
    }
    
    missing = []
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {name} installed")
        except ImportError:
            print(f"✗ {name} NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed!")
        return True


def check_api_key():
    """Check if OpenAI API key is set"""
    print("\nChecking OpenAI API key...")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("✗ OPENAI_API_KEY not found in environment")
        print("  1. Create a .env file from .env.example")
        print("  2. Add your OpenAI API key to .env")
        return False
    elif api_key == "your-openai-api-key-here":
        print("✗ OPENAI_API_KEY is still the placeholder value")
        print("  Update .env with your actual API key")
        return False
    else:
        print(f"✓ API key found (sk-...{api_key[-4:]})")
        return True


def check_database():
    """Check if database file exists"""
    print("\nChecking database...")
    db_path = "ecommerce.db"
    
    if not os.path.exists(db_path):
        print(f"✗ Database file '{db_path}' not found")
        print("  Run: python db_init.py")
        return False
    else:
        # Check if database has tables
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        if len(tables) == 0:
            print(f"✗ Database exists but has no tables")
            print("  Run: python db_init.py")
            return False
        else:
            print(f"✓ Database found with {len(tables)} tables")
            return True


def test_agent():
    """Test the Text2SQL agent with a simple query"""
    print("\nTesting Text2SQL agent...")
    
    try:
        from text2sql_agent import process_question
        
        # Simple test question
        test_question = "How many customers are there?"
        print(f"  Question: {test_question}")
        
        result = process_question(test_question)
        
        if result.get('error'):
            print(f"✗ Agent test failed: {result['error']}")
            return False
        else:
            print(f"  SQL: {result['sql_query']}")
            print(f"  Answer: {result['final_answer'][:100]}...")
            print("✓ Agent test passed!")
            return True
            
    except Exception as e:
        print(f"✗ Agent test failed with error: {str(e)}")
        return False


def main():
    """Run all checks"""
    print("="*60)
    print("Text2SQL Chatbot - Setup Verification")
    print("="*60)
    
    checks = [
        check_dependencies(),
        check_api_key(),
        check_database()
    ]
    
    if all(checks):
        print("\n" + "="*60)
        print("Running agent test...")
        print("="*60)
        test_agent()
    
    print("\n" + "="*60)
    if all(checks):
        print("✅ Setup complete! You're ready to go!")
        print("\nRun the chatbot with: chainlit run app.py")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
    print("="*60)


if __name__ == "__main__":
    main()
