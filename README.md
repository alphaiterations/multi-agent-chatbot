# Text2SQL Chatbot with LangGraph + Graph Visualization

A conversational AI chatbot that converts natural language questions into SQL queries and retrieves data from an e-commerce database. **Now with intelligent graph visualization!** Built with LangGraph for agent orchestration, OpenAI GPT-4o-mini for intelligence, and Chainlit for an interactive web interface.

## ✨ New Feature: Automatic Graph Generation

The chatbot now intelligently determines when a visualization would enhance understanding and automatically generates appropriate charts (bar, line, pie, scatter) alongside text answers!

**Example:**
- ❌ "How many orders in 2018?" → Text answer only
- ✅ "Yearly breakdown of orders" → Text answer + Line/Bar chart

📖 See [GRAPH_QUICKSTART.md](GRAPH_QUICKSTART.md) for details!

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface (Chainlit)                │
│                    Natural Language Questions                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Multi-Agent Workflow                  │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ SQL Generator│───▶│ SQL Executor │───▶│Answer Generator│
│  │   (GPT-4o)   │    │   (SQLite)   │    │   (GPT-4o)    │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                      │        │
│         │                    ▼                      ▼        │
│         │            ┌──────────────┐    ┌──────────────┐  │
│         └───────────▶│Error Handler │    │ Graph Agent  │⭐│
│                      │  & Retry     │    │ (Matplotlib) │  │
│                      └──────────────┘    └──────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  SQLite Database │
                │  (ecommerce.db)  │
                └─────────────────┘
```

### Component Details

#### 1. **User Interface (Chainlit)**
- **File:** `app.py`
- **Purpose:** Provides a web-based chat interface for users to ask questions
- **Features:**
  - Real-time chat interface
  - Displays generated SQL queries
  - Shows formatted results
  - **NEW:** Displays interactive graphs inline
  - Error handling and user feedback

#### 2. **LangGraph Agent Workflow**
- **File:** `text2sql_agent.py`
- **Purpose:** Orchestrates the text-to-SQL conversion process using a state graph
- **Workflow Nodes:**

  **a. SQL Generator Node**
  - Receives natural language question
  - Uses GPT-4o-mini to generate SQL query
  - Incorporates database schema knowledge
  - Returns syntactically correct SQLite query

  **b. SQL Executor Node**
  - Executes generated SQL against SQLite database
  - Fetches and formats results
  - Handles query errors
  - Returns structured data or error messages

  **c. Error Handler Node**
  - Activated when SQL execution fails
  - Analyzes error messages
  - Regenerates corrected SQL query
  - Implements retry logic (max 3 attempts)

  **d. Answer Generator Node**
  - Takes query results and original question
  - Uses GPT-4o-mini to create natural language response
  - Formats data for user readability
  - Provides insights and summaries

#### 3. **Database Layer**
- **File:** `db_init.py`
- **Database:** SQLite (`ecommerce.db`)
- **Schema:** Brazilian e-commerce dataset with 9 tables
  - `customers`: Customer information and locations
  - `orders`: Order details and timestamps
  - `order_items`: Items within each order
  - `order_payments`: Payment information
  - `order_reviews`: Customer reviews and ratings
  - `products`: Product catalog and attributes
  - `sellers`: Seller information
  - `geolocation`: Geographic coordinates
  - `product_category_name_translation`: Category translations

### Agent State Flow

The LangGraph workflow maintains the following state:

```python
AgentState = {
    "question": str,        # User's natural language question
    "sql_query": str,       # Generated SQL query
    "query_result": str,    # Execution results (JSON format)
    "final_answer": str,    # Natural language answer
    "error": str,           # Error messages if any
    "iteration": int        # Retry counter for error handling
}
```

### Control Flow

```
User Question
     │
     ▼
[Generate SQL] ────────────────────┐
     │                             │
     ▼                             │
[Execute SQL]                      │
     │                             │
     ├─── Success ──▶ [Generate Answer] ──▶ Return to User
     │                                             
     └─── Error ──▶ [Error Handler] ────────────┘
                    (retry up to 3x)
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Git (optional)

### Installation

1. **Clone or navigate to the repository:**
   ```bash
   cd /Users/vijendra/multi-agent-chatbot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

4. **Initialize the database:**
   ```bash
   python db_init.py
   ```
   
   This will create `ecommerce.db` with sample e-commerce data.

### Running the Application

**Start the Chainlit interface:**
```bash
chainlit run app.py
```

The application will open in your browser at `http://localhost:8000`

## 💬 Usage Examples

### Sample Questions

1. **Order Analytics:**
   - "How many orders were delivered?"
   - "Show me the top 10 orders by total value"
   - "What's the average delivery time?"

2. **Customer Insights:**
   - "How many customers are from São Paulo?"
   - "Which cities have the most customers?"

3. **Product Analysis:**
   - "What are the top 5 product categories by number of orders?"
   - "Show me products with the highest average review scores"

4. **Revenue Queries:**
   - "What's the total revenue from credit card payments?"
   - "Show me monthly revenue trends"

5. **Review Analysis:**
   - "What's the average review score across all orders?"
   - "How many orders have 5-star reviews?"

## 🛠️ Technical Details

### Why LangGraph?

LangGraph is used instead of LangChain for several key advantages:

1. **Explicit State Management:** Clear state definition and transitions
2. **Graph-based Workflows:** Visual and logical flow representation
3. **Better Error Handling:** Built-in retry and error recovery mechanisms
4. **Composability:** Easy to add new nodes and modify workflow
5. **Debugging:** Easier to trace and debug agent behavior

### Model Selection

- **GPT-4o-mini**: Chosen for balance of cost, speed, and accuracy
- Excellent SQL generation capabilities
- Fast response times for interactive chat
- Cost-effective for production use

### Key Features

1. **Automatic SQL Generation:** Converts natural language to SQL
2. **Error Recovery:** Self-correcting SQL queries on failures
3. **Schema Awareness:** Built-in knowledge of database structure
4. **Natural Language Responses:** Human-readable answers
5. **Interactive UI:** Real-time chat interface with Chainlit
6. **Query Transparency:** Shows generated SQL to users

## 📁 Project Structure

```
multi-agent-chatbot/
├── app.py                      # Chainlit frontend application
├── text2sql_agent.py           # LangGraph agent implementation
├── db_init.py                  # Database initialization script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
├── .env.example                # Environment template
├── README.md                   # This file
├── ecommerce.db               # SQLite database (generated)
└── data/                       # Raw CSV datasets
    ├── olist_customers_dataset.csv
    ├── olist_orders_dataset.csv
    ├── olist_order_items_dataset.csv
    ├── olist_order_payments_dataset.csv
    ├── olist_order_reviews_dataset.csv
    ├── olist_products_dataset.csv
    ├── olist_sellers_dataset.csv
    ├── olist_geolocation_dataset.csv
    └── product_category_name_translation.csv
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |

### Database Configuration

- **Database File:** `ecommerce.db` (SQLite)
- **Location:** Root directory
- **Regeneration:** Run `python db_init.py` to recreate

## 🧪 Testing

Test the agent independently:

```bash
python text2sql_agent.py
```

This runs a sample query to verify the setup.

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'langgraph'"**
   - Solution: `pip install -r requirements.txt`

2. **"Database file not found"**
   - Solution: Run `python db_init.py`

3. **"OpenAI API key not found"**
   - Solution: Create `.env` file with `OPENAI_API_KEY`

4. **SQL Execution Errors**
   - The agent will automatically retry with corrected queries
   - Check the error message in the chat interface

### Debug Mode

To see detailed logs, modify `app.py`:
```python
import chainlit as cl
cl.run(debug=True)
```

## 📊 Database Schema Reference

See the complete schema documentation in `text2sql_agent.py` under `SCHEMA_INFO`.

## 🚦 Performance Considerations

- **Query Limits:** Default LIMIT 10 for large result sets
- **Retry Logic:** Maximum 3 retry attempts for failed queries
- **Response Time:** Typically 2-5 seconds per query
- **Token Usage:** ~500-1000 tokens per question

## 🔒 Security Notes

- Never commit `.env` file to version control
- API keys should be kept secret
- SQL injection protection through parameterized queries
- Read-only database operations recommended for production

## 📝 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📧 Contact

For questions or support, please open an issue in the repository.

---

**Built with:**
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [OpenAI GPT-4o-mini](https://openai.com/) - Natural language processing
- [Chainlit](https://chainlit.io/) - Interactive UI
- [SQLite](https://www.sqlite.org/) - Database engine
