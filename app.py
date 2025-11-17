"""
Chainlit Frontend for Text2SQL Chatbot with Graph Visualization
"""

import chainlit as cl
from text2sql_agent import process_question, generat_graph
import os

# Set page configuration
@cl.on_chat_start
async def start():
    """Initialize the chat session"""
    
    # Generate the LangGraph workflow visualization
    try:
        workflow_diagram_path = generat_graph("text2sql_workflow.png")
        if workflow_diagram_path:
            print(f"✅ Workflow diagram generated: {workflow_diagram_path}")
    except Exception as e:
        print(f"⚠️ Warning: Could not generate workflow diagram: {e}")
    
    await cl.Message(
        content="👋 Welcome to the Text2SQL E-commerce Assistant!\n\n"
                "I can help you query the e-commerce database using natural language. "
                "Just ask me questions about:\n"
                "- Orders and their status\n"
                "- Customers and their locations\n"
                "- Products and categories\n"
                "- Payments and transactions\n"
                "- Reviews and ratings\n"
                "- Sellers and their information\n\n"
                "**Example questions:**\n"
                "- How many orders were delivered?\n"
                "- What are the top 5 product categories by sales?\n"
                "- Show me orders from São Paulo\n"
                "- What's the average review score?\n"
                "- Which sellers have the most orders?\n\n"
                "Go ahead and ask me anything! 🚀"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages"""
    
    user_question = message.content
    
    # Send a processing message
    processing_msg = cl.Message(content="🔍 Processing your question...")
    await processing_msg.send()
    
    try:
        # Process the question using the Text2SQL agent
        result = process_question(user_question)
        
        # Build the response content
        response_content = f"""**Your Question:** {result['question']}

**Generated SQL Query:**
```sql
{result['sql_query']}
```

**Answer:**
{result['final_answer']}
"""
        
        # If there was an error, include it
        if result.get('error'):
            response_content += f"\n\n⚠️ **Note:** {result['error']}"
        
        # Remove processing message and send final response
        await processing_msg.remove()
        
        # Send text response
        await cl.Message(content=response_content).send()
        
        # Send graph if available
        if result.get('needs_graph') and result.get('graph_image'):
            import base64
            
            # Decode base64 image
            image_data = base64.b64decode(result['graph_image'])
            
            # Create image element
            graph_element = cl.Image(
                name=f"{result.get('graph_type', 'chart')}_visualization",
                content=image_data,
                display="inline",
                size="large"
            )
            
            # Send graph with caption
            await cl.Message(
                content=f"📊 **Visualization ({result.get('graph_type', 'chart').title()} Chart)**",
                elements=[graph_element]
            ).send()
        
    except Exception as e:
        error_message = f"❌ An error occurred: {str(e)}\n\nPlease make sure:\n1. The database file exists (run `python db_init.py` first)\n2. Your OPENAI_API_KEY is set in the .env file"
        await processing_msg.remove()
        await cl.Message(content=error_message).send()


@cl.on_chat_end
async def end():
    """Handle chat end"""
    await cl.Message(content="Thanks for using the Text2SQL Assistant! 👋").send()


if __name__ == "__main__":
    # Run with: chainlit run app.py
    pass
