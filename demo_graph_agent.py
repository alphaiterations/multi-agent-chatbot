"""
Example Usage: Graph Agent Demo

This script demonstrates the graph agent functionality with various query types.
Run this to see how the chatbot decides when to generate graphs.
"""

from text2sql_agent import process_question
import json


def demo_query(question: str, description: str):
    """Run a demo query and display results"""
    print("=" * 80)
    print(f"DEMO: {description}")
    print("=" * 80)
    print(f"Question: {question}\n")
    
    try:
        result = process_question(question)
        
        print(f"SQL Query Generated:")
        print(f"  {result['sql_query']}\n")
        
        print(f"Answer:")
        print(f"  {result['final_answer']}\n")
        
        print(f"Graph Decision:")
        print(f"  Needs Graph: {result['needs_graph']}")
        print(f"  Graph Type: {result['graph_type'] if result['graph_type'] else 'None'}")
        
        if result['graph_image']:
            print(f"  Graph Generated: ✅ Yes ({len(result['graph_image'])} chars)")
        else:
            print(f"  Graph Generated: ❌ No")
            
        if result.get('error'):
            print(f"\n⚠️  Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║           GRAPH AGENT DEMONSTRATION                             ║
║   Intelligent Chart Generation for Text2SQL Queries            ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Test Case 1: Simple Count - Should NOT generate graph
    demo_query(
        "How many orders were delivered?",
        "Simple Count Query (No Graph Expected)"
    )
    
    # Test Case 2: Yearly Breakdown - Should generate BAR or LINE chart
    demo_query(
        "Can you give me yearly breakdown of the orders?",
        "Yearly Breakdown (Graph Expected - Line/Bar)"
    )
    
    # Test Case 3: Top Categories - Should generate BAR chart
    demo_query(
        "What are the top 5 product categories by number of orders?",
        "Top Categories (Graph Expected - Bar)"
    )
    
    # Test Case 4: Distribution - Should generate PIE chart
    demo_query(
        "Show me the distribution of order statuses",
        "Status Distribution (Graph Expected - Pie)"
    )
    
    # Test Case 5: Average - Should NOT generate graph
    demo_query(
        "What is the average order value?",
        "Average Value (No Graph Expected)"
    )
    
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nKey Observations:")
    print("✓ Simple queries (counts, averages) → No graph")
    print("✓ Breakdown/trend queries → Line or bar chart")
    print("✓ Distribution queries → Pie chart")
    print("✓ Comparison queries → Bar chart")
    print("\nThe AI intelligently decides based on:")
    print("  - Question semantics")
    print("  - Data structure")
    print("  - Visualization value")
    print()
