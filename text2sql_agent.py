"""
Text2SQL Agent using LangGraph
This module implements a multi-agent system for converting natural language to SQL queries.
"""

import os
import sqlite3
from typing import TypedDict, Annotated, Sequence, Optional
from langgraph.graph import StateGraph, END
from openai import OpenAI
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Database configuration
DB_PATH = "ecommerce.db"

# Database schema information
SCHEMA_INFO = """
Database Schema for E-commerce System:

1. customers
   - customer_id (TEXT): Unique customer identifier
   - customer_unique_id (TEXT): Unique customer identifier across datasets
   - customer_zip_code_prefix (INTEGER): Customer zip code
   - customer_city (TEXT): Customer city
   - customer_state (TEXT): Customer state

2. orders
   - order_id (TEXT): Unique order identifier
   - customer_id (TEXT): Foreign key to customers
   - order_status (TEXT): Order status (delivered, shipped, etc.)
   - order_purchase_timestamp (TEXT): When the order was placed
   - order_approved_at (TEXT): When payment was approved
   - order_delivered_carrier_date (TEXT): When order was handed to carrier
   - order_delivered_customer_date (TEXT): When customer received the order
   - order_estimated_delivery_date (TEXT): Estimated delivery date

3. order_items
   - order_id (TEXT): Foreign key to orders
   - order_item_id (INTEGER): Item sequence number within order
   - product_id (TEXT): Foreign key to products
   - seller_id (TEXT): Foreign key to sellers
   - shipping_limit_date (TEXT): Shipping deadline
   - price (REAL): Item price
   - freight_value (REAL): Shipping cost

4. order_payments
   - order_id (TEXT): Foreign key to orders
   - payment_sequential (INTEGER): Payment sequence number
   - payment_type (TEXT): Payment method (credit_card, boleto, etc.)
   - payment_installments (INTEGER): Number of installments
   - payment_value (REAL): Payment amount

5. order_reviews
   - review_id (TEXT): Unique review identifier
   - order_id (TEXT): Foreign key to orders
   - review_score (INTEGER): Review score (1-5)
   - review_comment_title (TEXT): Review title
   - review_comment_message (TEXT): Review message
   - review_creation_date (TEXT): When review was created
   - review_answer_timestamp (TEXT): When review was answered

6. products
   - product_id (TEXT): Unique product identifier
   - product_category_name (TEXT): Product category (in Portuguese)
   - product_name_lenght (REAL): Product name length
   - product_description_lenght (REAL): Product description length
   - product_photos_qty (REAL): Number of product photos
   - product_weight_g (REAL): Product weight in grams
   - product_length_cm (REAL): Product length in cm
   - product_height_cm (REAL): Product height in cm
   - product_width_cm (REAL): Product width in cm

7. sellers
   - seller_id (TEXT): Unique seller identifier
   - seller_zip_code_prefix (INTEGER): Seller zip code
   - seller_city (TEXT): Seller city
   - seller_state (TEXT): Seller state

8. geolocation
   - geolocation_zip_code_prefix (INTEGER): Zip code prefix
   - geolocation_lat (REAL): Latitude
   - geolocation_lng (REAL): Longitude
   - geolocation_city (TEXT): City name
   - geolocation_state (TEXT): State code

9. product_category_name_translation
   - product_category_name (TEXT): Category name in Portuguese
   - product_category_name_english (TEXT): Category name in English
"""


class AgentState(TypedDict):
    """State of the agent workflow"""
    question: str
    sql_query: str
    query_result: str
    final_answer: str
    error: str
    iteration: int
    needs_graph: bool
    graph_type: str
    graph_image: str


def generate_sql(state: AgentState) -> AgentState:
    """Generate SQL query from natural language question"""
    question = state["question"]
    iteration = state.get("iteration", 0)
    
    prompt = f"""You are a SQL expert. Convert the following natural language question into a valid SQLite query.

{SCHEMA_INFO}

Question: {question}

Important Guidelines:
1. Use only the tables and columns mentioned in the schema
2. Use proper JOIN clauses when querying multiple tables
3. Return ONLY the SQL query without any explanation or markdown formatting
4. Do not include semicolons at the end
5. Use aggregate functions (COUNT, SUM, AVG, etc.) appropriately
6. Add LIMIT clauses for queries that might return many rows (default LIMIT 10 unless user specifies)
7. Use proper WHERE clauses to filter data
8. For date comparisons, remember the dates are stored as TEXT in ISO format

Generate the SQL query:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a SQL expert. Generate only valid SQLite queries without any formatting or explanation."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    sql_query = response.choices[0].message.content.strip()
    # Remove markdown code blocks if present
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    
    state["sql_query"] = sql_query
    state["iteration"] = iteration + 1
    
    return state


def execute_sql(state: AgentState) -> AgentState:
    """Execute the generated SQL query"""
    sql_query = state["sql_query"]
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(sql_query)
        
        # Fetch results
        results = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        
        conn.close()
        
        # Format results
        if not results:
            state["query_result"] = "No results found."
        else:
            # Convert to list of dictionaries
            formatted_results = []
            for row in results[:100]:  # Limit to 100 rows for display
                formatted_results.append(dict(zip(column_names, row)))
            
            state["query_result"] = json.dumps(formatted_results, indent=2)
        
        state["error"] = ""
        
    except Exception as e:
        state["error"] = f"SQL Execution Error: {str(e)}"
        state["query_result"] = ""
    
    return state


def generate_answer(state: AgentState) -> AgentState:
    """Generate natural language answer from query results"""
    question = state["question"]
    sql_query = state["sql_query"]
    query_result = state["query_result"]
    
    prompt = f"""You are a helpful assistant that explains database query results in natural language.

Original Question: {question}

SQL Query Used: {sql_query}

Query Results:
{query_result}

Please provide a clear, concise answer to the original question based on the query results.
Format the answer in a user-friendly way. If the results contain numbers, present them clearly.
If there are multiple results, summarize them appropriately.

Answer:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that explains data insights clearly and concisely."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    final_answer = response.choices[0].message.content.strip()
    state["final_answer"] = final_answer
    
    return state


def decide_graph_need(state: AgentState) -> AgentState:
    """Decide if a graph visualization would be helpful for the query"""
    question = state["question"]
    query_result = state["query_result"]
    
    # If no results or error, no graph needed
    if not query_result or query_result == "No results found." or state.get("error"):
        state["needs_graph"] = False
        state["graph_type"] = ""
        return state
    
    prompt = f"""Analyze the following question and query results to determine if a graph visualization would be helpful.

Question: {question}

Query Results Sample:
{query_result[:500]}...

Determine:
1. Would a graph be helpful for this data? (YES/NO)
2. If yes, what type of graph? (bar, line, pie, scatter)

Consider:
- Trends over time → line chart
- Comparisons between categories → bar chart
- Proportions/percentages → pie chart
- Correlations → scatter plot
- Simple counts or single values → NO graph needed

Respond in JSON format:
{{"needs_graph": true/false, "graph_type": "bar/line/pie/scatter/none", "reason": "brief explanation"}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a data visualization expert. Analyze queries and determine if visualization would add value."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    decision = json.loads(response.choices[0].message.content)
    state["needs_graph"] = decision.get("needs_graph", False)
    state["graph_type"] = decision.get("graph_type", "none")
    
    return state


def generate_graph(state: AgentState) -> AgentState:
    """Generate a graph visualization from query results"""
    query_result = state["query_result"]
    graph_type = state["graph_type"]
    question = state["question"]
    
    try:
        # Parse query results
        results = json.loads(query_result)
        if not results or len(results) == 0:
            state["graph_image"] = ""
            return state
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Create figure
        plt.figure(figsize=(10, 6))
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Determine x and y columns
        columns = df.columns.tolist()
        
        if len(columns) >= 2:
            # Use first column for x-axis, second for y-axis
            x_col = columns[0]
            y_col = columns[1]
            
            # Limit to top 20 items for readability
            if len(df) > 20:
                df = df.head(20)
            
            if graph_type == "bar":
                plt.bar(range(len(df)), df[y_col], color='steelblue', alpha=0.8)
                plt.xticks(range(len(df)), df[x_col], rotation=45, ha='right')
                plt.ylabel(y_col.replace('_', ' ').title())
                plt.xlabel(x_col.replace('_', ' ').title())
                
            elif graph_type == "line":
                plt.plot(df[x_col], df[y_col], marker='o', linewidth=2, markersize=6, color='steelblue')
                plt.xlabel(x_col.replace('_', ' ').title())
                plt.ylabel(y_col.replace('_', ' ').title())
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3)
                
            elif graph_type == "pie":
                # Use top 10 for pie charts
                if len(df) > 10:
                    df = df.head(10)
                plt.pie(df[y_col], labels=df[x_col], autopct='%1.1f%%', startangle=90)
                plt.axis('equal')
                
            elif graph_type == "scatter":
                plt.scatter(df[x_col], df[y_col], alpha=0.6, s=100, color='steelblue')
                plt.xlabel(x_col.replace('_', ' ').title())
                plt.ylabel(y_col.replace('_', ' ').title())
                plt.grid(True, alpha=0.3)
        
        plt.title(question, fontsize=12, fontweight='bold', pad=20)
        plt.tight_layout()
        
        # Save to bytes buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        
        # Encode to base64
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        state["graph_image"] = image_base64
        
        plt.close()
        
    except Exception as e:
        print(f"Graph generation error: {e}")
        state["graph_image"] = ""
    
    return state


def handle_error(state: AgentState) -> AgentState:
    """Handle errors and attempt to fix the SQL query"""
    error = state["error"]
    sql_query = state["sql_query"]
    question = state["question"]
    iteration = state.get("iteration", 0)
    
    # If we've tried too many times, give up
    if iteration > 3:
        state["final_answer"] = f"I apologize, but I'm having trouble generating a correct SQL query for your question. Error: {error}"
        return state
    
    prompt = f"""The following SQL query failed with an error. Please fix it.

{SCHEMA_INFO}

Original Question: {question}

Failed SQL Query: {sql_query}

Error: {error}

Generate a corrected SQL query that will work. Return ONLY the SQL query without any explanation or markdown formatting:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a SQL expert. Fix the SQL query to resolve the error."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    corrected_query = response.choices[0].message.content.strip()
    corrected_query = corrected_query.replace("```sql", "").replace("```", "").strip()
    
    state["sql_query"] = corrected_query
    state["error"] = ""  # Clear the error for retry
    state["iteration"] = iteration + 1  # Increment iteration counter
    
    return state


def should_retry(state: AgentState) -> str:
    """Decide whether to retry after an error"""
    if state.get("error"):
        iteration = state.get("iteration", 0)
        if iteration <= 3:
            return "retry"
        else:
            return "end"
    return "success"


def should_generate_graph(state: AgentState) -> str:
    """Decide whether to generate a graph"""
    if state.get("needs_graph", False):
        return "generate_graph"
    return "skip_graph"


# Build the LangGraph workflow
def create_text2sql_graph():
    """Create the LangGraph state graph for Text2SQL with graph generation"""
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("generate_sql", generate_sql)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("handle_error", handle_error)
    workflow.add_node("decide_graph_need", decide_graph_need)
    workflow.add_node("generate_graph", generate_graph)
    
    # Add edges
    workflow.set_entry_point("generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    
    # Conditional edge based on execution success
    workflow.add_conditional_edges(
        "execute_sql",
        should_retry,
        {
            "success": "generate_answer",
            "retry": "handle_error",
            "end": "generate_answer"
        }
    )
    
    workflow.add_edge("handle_error", "execute_sql")
    workflow.add_edge("generate_answer", "decide_graph_need")
    
    # Conditional edge for graph generation
    workflow.add_conditional_edges(
        "decide_graph_need",
        should_generate_graph,
        {
            "generate_graph": "generate_graph",
            "skip_graph": END
        }
    )
    
    workflow.add_edge("generate_graph", END)
    
    return workflow.compile()


# Create the compiled graph
text2sql_graph = create_text2sql_graph()


def generat_graph(output_path: str = "text2sql_workflow.png") -> str:
    """
    Generate a PNG visualization of the LangGraph workflow.
    
    Args:
        output_path: Path where the PNG file will be saved (default: "text2sql_workflow.png")
    
    Returns:
        str: Path to the generated PNG file
    """
    try:
        from IPython.display import Image, display
        
        # Get the graph visualization
        graph_image = text2sql_graph.get_graph().draw_mermaid_png()
        
        # Save to file
        with open(output_path, "wb") as f:
            f.write(graph_image)
        
        print(f"Graph visualization saved to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating graph visualization: {e}")
        print("Make sure you have 'pygraphviz' or 'grandalf' installed:")
        print("  pip install pygraphviz")
        print("  or")
        print("  pip install grandalf")
        return None


def process_question(question: str) -> dict:
    """Process a natural language question and return SQL + answer + optional graph"""
    initial_state = AgentState(
        question=question,
        sql_query="",
        query_result="",
        final_answer="",
        error="",
        iteration=0,
        needs_graph=False,
        graph_type="",
        graph_image=""
    )
    
    # Invoke with increased recursion limit
    result = text2sql_graph.invoke(
        initial_state,
        config={"recursion_limit": 50}
    )
    
    return {
        "question": result["question"],
        "sql_query": result["sql_query"],
        "query_result": result["query_result"],
        "final_answer": result["final_answer"],
        "error": result.get("error", ""),
        "needs_graph": result.get("needs_graph", False),
        "graph_type": result.get("graph_type", ""),
        "graph_image": result.get("graph_image", "")
    }


if __name__ == "__main__":
    # Test the agent with and without graphs
    print("=" * 80)
    print("Test 1: Simple count (no graph expected)")
    print("=" * 80)
    test_question_1 = "How many orders were delivered?"
    result_1 = process_question(test_question_1)
    print(f"Question: {result_1['question']}")
    print(f"\nSQL Query: {result_1['sql_query']}")
    print(f"\nAnswer: {result_1['final_answer']}")
    print(f"\nNeeds Graph: {result_1['needs_graph']}")
    print(f"Graph Type: {result_1['graph_type']}")
    
    print("\n" + "=" * 80)
    print("Test 2: Breakdown query (graph expected)")
    print("=" * 80)
    test_question_2 = "Can you give me yearly breakdown of the orders?"
    result_2 = process_question(test_question_2)
    print(f"Question: {result_2['question']}")
    print(f"\nSQL Query: {result_2['sql_query']}")
    print(f"\nAnswer: {result_2['final_answer']}")
    print(f"\nNeeds Graph: {result_2['needs_graph']}")
    print(f"Graph Type: {result_2['graph_type']}")
    if result_2['graph_image']:
        print(f"Graph Image: Generated (base64 encoded, {len(result_2['graph_image'])} characters)")

