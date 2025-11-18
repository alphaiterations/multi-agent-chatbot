"""
Text2SQL Agent using LangGraph
This module implements an Agentic system for converting natural language to SQL queries and also generates graphs.
"""

import os
import sqlite3
from typing import TypedDict
from langgraph.graph import StateGraph, END
from openai import OpenAI
import json
import pandas as pd

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
    graph_json: str  # Plotly figure JSON for Chainlit
    is_in_scope: bool  # Whether the question is about e-commerce data


def check_guardrails(state: AgentState) -> AgentState:
    """Check if the question is within scope (e-commerce related)"""
    question = state["question"]
    
    prompt = f"""You are a guardrails system for an e-commerce database chatbot. Your job is to determine if a user's question is related to e-commerce data, if it's a greeting, or if it's out of scope.

The chatbot has access to an e-commerce database with information about:
- Customers and their locations
- Orders and order status (data from 2016-2018)
- Products and categories
- Sellers
- Payments
- Reviews
- Shipping and delivery information

Examples of GREETING messages:
- "Hi", "Hello", "Hey"
- "Good morning", "Good afternoon"
- "How are you?"
- Any casual greeting or introduction

Examples of IN-SCOPE questions:
- "How many orders were placed last month?"
- "What are the top selling products?"
- "Show me customer distribution by state"
- "What is the average order value?"
- "Which sellers have the highest ratings?"

Examples of OUT-OF-SCOPE questions:
- Personal questions (e.g., "What is my wife's name?", "Where do I live?")
- Political questions (e.g., "Who should I vote for?", "What do you think about the president?")
- General knowledge (e.g., "What is the capital of France?", "How does photosynthesis work?")
- Unrelated topics (e.g., "Tell me a joke", "What's the weather like?")

User Question: {question}

Analyze the question and respond in JSON format:
{{
    "is_in_scope": true/false,
    "is_greeting": true/false,
    "reason": "brief explanation of why it is or isn't in scope or if it's a greeting"
}}

If the question is a greeting, mark is_greeting as true and is_in_scope as false.
If the question is ambiguous but could potentially relate to the e-commerce data, mark it as in_scope."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a guardrails system that filters questions to ensure they are relevant to e-commerce data analysis or identifies greetings."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    state["is_in_scope"] = result.get("is_in_scope", False)
    is_greeting = result.get("is_greeting", False)
    
    # If it's a greeting, provide a welcome message
    if is_greeting:
        state["final_answer"] = "Hi! I am your e-commerce assistant. I can answer all the queries related to orders, customers, products, sellers, payments, and reviews between 2016-2018. How can I help you today?"
        return state
    
    # If out of scope, set the final answer immediately
    if not state["is_in_scope"]:
        state["final_answer"] = "I apologize, but your question appears to be out of scope. I can only answer questions about the e-commerce data, including:\n\n- Customer information and locations\n- Orders and order status\n- Products and categories\n- Sellers and their performance\n- Payment information\n- Reviews and ratings\n- Shipping and delivery data\n\nPlease ask a question related to the e-commerce database."
    
    return state


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
4. If the question contains multiple sub-questions, generate separate SQL queries separated by semicolons
5. Use aggregate functions (COUNT, SUM, AVG, etc.) appropriately
6. Add LIMIT clauses for queries that might return many rows (default LIMIT 10 unless user specifies)
7. Use proper WHERE clauses to filter data
8. For date comparisons, remember the dates are stored as TEXT in ISO format
9. Each SQL statement should be on its own line for clarity when multiple queries are needed

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
    """Execute the generated SQL query (handles multiple queries if present)"""
    sql_query = state["sql_query"]
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Split multiple SQL statements (separated by semicolons)
        # Remove empty statements and strip whitespace
        sql_statements = [stmt.strip() for stmt in sql_query.split(';') if stmt.strip()]
        
        all_results = []
        
        # Execute each statement separately
        for i, statement in enumerate(sql_statements):
            cursor.execute(statement)
            
            # Fetch results for this statement
            results = cursor.fetchall()
            
            if results:
                column_names = [description[0] for description in cursor.description]
                
                # Convert to list of dictionaries
                formatted_results = []
                for row in results[:100]:  # Limit to 100 rows per query
                    formatted_results.append(dict(zip(column_names, row)))
                
                # If multiple queries, label them
                if len(sql_statements) > 1:
                    all_results.append({
                        f"query_{i+1}": formatted_results,
                        f"query_{i+1}_sql": statement
                    })
                else:
                    all_results = formatted_results
        
        conn.close()
        
        # Format results
        if not all_results:
            state["query_result"] = "No results found."
        else:
            state["query_result"] = json.dumps(all_results, indent=2)
        
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
If there are multiple queries/results (for multi-part questions), address each part of the question separately.
Use bullet points or numbered lists for multiple answers.

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
    """Generate a graph visualization from query results using LLM-generated Plotly code"""
    query_result = state["query_result"]
    graph_type = state["graph_type"]
    question = state["question"]
    
    try:
        # Parse query results
        results = json.loads(query_result)
        if not results or len(results) == 0:
            state["graph_json"] = ""
            return state
        
        # Convert to DataFrame for context
        df = pd.DataFrame(results)
        columns = df.columns.tolist()
        sample_data = df.head(5).to_dict('records')
        
        # Generate Plotly code using LLM
        prompt = f"""Generate Python code using Plotly to visualize the following data.

Question: {question}
Graph Type: {graph_type}
Columns: {columns}
Sample Data (first 5 rows): {json.dumps(sample_data, indent=2)}
Total Rows: {len(df)}

Requirements:
1. Use plotly.graph_objects or plotly.express
2. The data is already loaded as 'df' (a pandas DataFrame)
3. Create an appropriate {graph_type} chart
4. Limit data to top 20 rows if there are many rows
5. Add proper titles, labels, and formatting
6. The figure variable must be named 'fig'
7. Return ONLY the Python code, no explanations or markdown
8. Do NOT include any import statements
9. Do NOT include code to show the figure (no fig.show())
10. Make the visualization visually appealing with appropriate colors and layout
11. Update the layout for better interactivity (hover info, responsive sizing)

Generate the Plotly code:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data visualization expert. Generate clean, executable Plotly code without any markdown formatting or explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        plotly_code = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        plotly_code = plotly_code.replace("```python", "").replace("```", "").strip()
        
        # Prepare execution environment
        exec_globals = {
            'df': df,
            'pd': pd,
            'json': json
        }
        
        # Import plotly dynamically
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            exec_globals['go'] = go
            exec_globals['px'] = px
        except ImportError:
            print("Plotly not installed. Installing...")
            import subprocess
            subprocess.check_call(['pip', 'install', 'plotly'])
            import plotly.graph_objects as go
            import plotly.express as px
            exec_globals['go'] = go
            exec_globals['px'] = px
        
        # Execute the generated code
        exec(plotly_code, exec_globals)
        
        # Get the figure object
        fig = exec_globals.get('fig')
        
        if fig is None:
            raise ValueError("Generated code did not create a 'fig' variable")
        
        # Export figure as JSON for Chainlit's Plotly element
        graph_json = fig.to_json()
        state["graph_json"] = graph_json
        
    except Exception as e:
        print(f"Graph generation error: {e}")
        print(f"Generated code:\n{plotly_code if 'plotly_code' in locals() else 'No code generated'}")
        state["graph_json"] = ""
    
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


def check_scope(state: AgentState) -> str:
    """Check if question is in scope to continue processing"""
    if state.get("is_in_scope", True):
        return "in_scope"
    return "out_of_scope"


# Build the LangGraph workflow
def create_text2sql_graph():
    """Create the LangGraph state graph for Text2SQL with graph generation"""
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("check_guardrails", check_guardrails)
    workflow.add_node("generate_sql", generate_sql)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("handle_error", handle_error)
    workflow.add_node("decide_graph_need", decide_graph_need)
    workflow.add_node("generate_graph", generate_graph)
    
    # Add edges - start with guardrails check
    workflow.set_entry_point("check_guardrails")
    
    # Conditional edge from guardrails - only proceed if in scope
    workflow.add_conditional_edges(
        "check_guardrails",
        check_scope,
        {
            "in_scope": "generate_sql",
            "out_of_scope": END
        }
    )
    
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


def generate_graph_visualization(output_path: str = "text2sql_workflow.png") -> str:
    """
    Generate a PNG visualization of the LangGraph workflow.
    
    Args:
        output_path: Path where the PNG file will be saved (default: "text2sql_workflow.png")
    
    Returns:
        str: Path to the generated PNG file
    """
    try:
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


async def process_question_stream(question: str):
    """
    Process a natural language question and stream node execution events.
    This is an async generator that yields node events for debugging visualization.
    
    Yields:
        dict: Event with type ('node_start', 'node_end', 'error', 'final') and data
    """
    initial_state = AgentState(
        question=question,
        sql_query="",
        query_result="",
        final_answer="",
        error="",
        iteration=0,
        needs_graph=False,
        graph_type="",
        graph_json="",
        is_in_scope=True
    )
    
    current_state = initial_state.copy()
    
    try:
        # Stream events from the graph
        async for event in text2sql_graph.astream_events(
            initial_state,
            config={"recursion_limit": 50},
            version="v1"
        ):
            event_type = event.get("event")
            
            # Node start event
            if event_type == "on_chain_start":
                node_name = event.get("name", "")
                if node_name in ["check_guardrails", "generate_sql", "execute_sql", "generate_answer", 
                               "handle_error", "decide_graph_need", "generate_graph"]:
                    yield {
                        "type": "node_start",
                        "node": node_name,
                        "input": current_state
                    }
            
            # Node end event
            elif event_type == "on_chain_end":
                node_name = event.get("name", "")
                if node_name in ["check_guardrails", "generate_sql", "execute_sql", "generate_answer", 
                               "handle_error", "decide_graph_need", "generate_graph"]:
                    output = event.get("data", {}).get("output", {})
                    if output:
                        current_state.update(output)
                        yield {
                            "type": "node_end",
                            "node": node_name,
                            "output": output,
                            "state": current_state.copy()
                        }
        
        # Send final result
        yield {
            "type": "final",
            "result": current_state
        }
        
    except Exception as e:
        yield {
            "type": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    # Test the agent
    print("=" * 80)
    print("Text2SQL Agent - Use 'chainlit run app.py' to start the web interface")
    print("=" * 80)
    print("\nThis module is meant to be imported and used via the Chainlit app.")
    print("Run: chainlit run app.py")

