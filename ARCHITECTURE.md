# Text2SQL Chatbot - Architecture Documentation

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    Chainlit Web UI (app.py)                 │    │
│  │  • Real-time chat interface                                 │    │
│  │  • Display SQL queries & results                            │    │
│  │  • Error handling & user feedback                           │    │
│  └────────────────────┬───────────────────────────────────────┘    │
└─────────────────────────┼────────────────────────────────────────────┘
                          │ Natural Language Question
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AGENT ORCHESTRATION LAYER                       │
│                   LangGraph Workflow (text2sql_agent.py)            │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    STATE GRAPH WORKFLOW                       │  │
│  │                                                               │  │
│  │   ┌────────────────┐                                         │  │
│  │   │  Entry Point   │                                         │  │
│  │   │  (Question)    │                                         │  │
│  │   └───────┬────────┘                                         │  │
│  │           │                                                   │  │
│  │           ▼                                                   │  │
│  │   ┌────────────────┐         Agent State                     │  │
│  │   │ SQL Generator  │         ├─ question: str                │  │
│  │   │  Node (GPT-4o) │         ├─ sql_query: str               │  │
│  │   └───────┬────────┘         ├─ query_result: str            │  │
│  │           │                  ├─ final_answer: str            │  │
│  │           ▼                  ├─ error: str                   │  │
│  │   ┌────────────────┐         └─ iteration: int               │  │
│  │   │ SQL Executor   │                                         │  │
│  │   │  Node (SQLite) │                                         │  │
│  │   └───────┬────────┘                                         │  │
│  │           │                                                   │  │
│  │           ├──── Success ────▶┌────────────────┐             │  │
│  │           │                   │Answer Generator│             │  │
│  │           │                   │  Node (GPT-4o) │             │  │
│  │           │                   └───────┬────────┘             │  │
│  │           │                           │                      │  │
│  │           │                           ▼                      │  │
│  │           │                      ┌─────────┐                │  │
│  │           │                      │   END   │                │  │
│  │           │                      └─────────┘                │  │
│  │           │                                                   │  │
│  │           └──── Error ─────▶┌────────────────┐              │  │
│  │                              │ Error Handler  │              │  │
│  │                              │   Node (GPT)   │              │  │
│  │                              └───────┬────────┘              │  │
│  │                                      │                       │  │
│  │                                      │ Retry (max 3x)        │  │
│  │                                      └──────┐                │  │
│  │                                             │                │  │
│  │                              ┌──────────────┘                │  │
│  │                              │                               │  │
│  │                              ▼                               │  │
│  │                      ┌────────────────┐                      │  │
│  │                      │ SQL Executor   │                      │  │
│  │                      │ (Retry)        │                      │  │
│  │                      └────────────────┘                      │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬────────────────────────────────────────────┘
                          │ SQL Query
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              SQLite Database (ecommerce.db)                 │    │
│  │                                                              │    │
│  │  Tables:                                                     │    │
│  │  • customers         • order_items                           │    │
│  │  • orders            • order_payments                        │    │
│  │  • products          • order_reviews                         │    │
│  │  • sellers           • geolocation                           │    │
│  │  • product_category_name_translation                         │    │
│  └────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Question Processing Flow
```
User Input → Chainlit UI → LangGraph Agent → OpenAI API → SQL Query
```

### 2. Query Execution Flow
```
SQL Query → SQLite Database → Results → JSON Format → State Update
```

### 3. Answer Generation Flow
```
Query Results + Original Question → OpenAI API → Natural Language Answer → User
```

### 4. Error Recovery Flow
```
SQL Error → Error Handler → Analyze Error → Generate Fixed SQL → Retry (max 3x)
```

## Component Responsibilities

### Chainlit (app.py)
**Responsibilities:**
- Render web-based chat interface
- Handle user input and display responses
- Show SQL queries for transparency
- Manage chat session lifecycle
- Display errors in user-friendly format

**Technology:** Chainlit framework

---

### LangGraph Agent (text2sql_agent.py)
**Responsibilities:**
- Orchestrate multi-node workflow
- Maintain agent state across nodes
- Route between nodes based on conditions
- Implement retry logic for failures
- Manage conversation context

**Technology:** LangGraph state graph

---

### SQL Generator Node
**Responsibilities:**
- Parse natural language questions
- Understand database schema
- Generate syntactically correct SQL
- Apply best practices (LIMIT, JOINs, etc.)
- Handle complex query requirements

**Technology:** OpenAI GPT-4o-mini

---

### SQL Executor Node
**Responsibilities:**
- Execute SQL queries safely
- Fetch and format results
- Handle query errors gracefully
- Limit result size for performance
- Return structured data

**Technology:** SQLite3

---

### Error Handler Node
**Responsibilities:**
- Analyze SQL execution errors
- Generate corrected SQL queries
- Implement exponential backoff
- Track retry attempts
- Fail gracefully after max retries

**Technology:** OpenAI GPT-4o-mini + Logic

---

### Answer Generator Node
**Responsibilities:**
- Convert JSON results to natural language
- Summarize large result sets
- Provide insights from data
- Format numbers and dates
- Create user-friendly responses

**Technology:** OpenAI GPT-4o-mini

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Chainlit | Interactive web UI |
| Orchestration | LangGraph | Agent workflow management |
| AI/LLM | OpenAI GPT-4o-mini | SQL generation & NL processing |
| Database | SQLite | Data storage and querying |
| Language | Python 3.8+ | Core implementation |
| State Management | LangGraph TypedDict | Type-safe state handling |

## Design Patterns

### 1. State Machine Pattern
LangGraph implements a state machine where each node transforms the state and routes to the next node based on conditions.

### 2. Retry Pattern
Error handling uses automatic retry with a maximum attempt limit to handle transient failures.

### 3. Chain of Responsibility
Each node in the graph is responsible for a specific task, passing the state to the next node.

### 4. Template Method Pattern
The agent workflow follows a consistent template: Generate → Execute → Handle → Respond.

## Security Considerations

1. **API Key Protection**: Stored in `.env` file, never committed to version control
2. **SQL Injection Prevention**: Uses parameterized queries where possible
3. **Query Validation**: AI-generated SQL is validated before execution
4. **Result Limiting**: Automatic LIMIT clauses prevent excessive data retrieval
5. **Error Sanitization**: Errors are sanitized before display to users

## Performance Optimizations

1. **Query Limits**: Default LIMIT 10 to prevent large result sets
2. **Retry Logic**: Maximum 3 retries to prevent infinite loops
3. **Result Truncation**: Large results truncated to first 100 rows
4. **Token Optimization**: Concise prompts to minimize API costs
5. **Stateless Execution**: Each query is independent for parallelization

## Scalability Considerations

### Current Implementation (SQLite)
- Suitable for: Development, demos, small-scale applications
- Limitations: Single-threaded writes, limited concurrency
- Max scale: ~100 concurrent users

### Production Recommendations
For production at scale, consider:
1. **Database**: Migrate to PostgreSQL or MySQL
2. **Caching**: Add Redis for frequent queries
3. **Load Balancing**: Deploy multiple instances
4. **Queue System**: Add Celery for async processing
5. **Monitoring**: Implement logging and metrics

## Monitoring & Debugging

### Logging Points
1. User question received
2. SQL query generated
3. Query execution status
4. Error occurrences
5. Final answer generated

### Key Metrics
- Average response time
- SQL generation accuracy
- Query success rate
- Retry frequency
- User satisfaction (reviews)

## Future Enhancements

1. **Multi-turn Conversations**: Remember context across questions
2. **Query Optimization**: Suggest indexes and optimizations
3. **Visualization**: Generate charts from query results
4. **Export Features**: Allow CSV/Excel export of results
5. **User Feedback Loop**: Learn from corrections
6. **Advanced Analytics**: Support for complex aggregations
7. **Natural Language Filters**: Dynamic WHERE clause generation

---

**Last Updated:** November 2025
**Version:** 1.0
