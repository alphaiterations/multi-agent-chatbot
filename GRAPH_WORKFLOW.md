# Graph Agent Flow Diagram

## Complete Workflow with Graph Generation

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER ASKS QUESTION                        │
│     "Can you give me yearly breakdown of the orders?"           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Generate SQL   │
                    │  (GPT-4o-mini) │
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Execute SQL   │
                    │    (SQLite)    │
                    └────────┬───────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
            (Success)              (Error)
                  │                     │
                  │                     ▼
                  │            ┌────────────────┐
                  │            │ Handle Error & │
                  │            │  Fix SQL       │
                  │            └────────┬───────┘
                  │                     │
                  │                     │ (Retry up to 3x)
                  │                     │
                  │    ┌────────────────┘
                  ▼    ▼
         ┌────────────────────┐
         │  Generate Answer   │
         │   (GPT-4o-mini)    │
         │  Natural Language  │
         └──────────┬─────────┘
                    │
                    ▼
         ┌────────────────────┐
         │ Decide Graph Need  │ ⭐ NEW
         │   (GPT-4o-mini)    │
         │                    │
         │ Analyzes:          │
         │ • Question type    │
         │ • Data structure   │
         │ • Value add        │
         └──────────┬─────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
   (needs_graph=true)      (needs_graph=false)
        │                       │
        ▼                       │
┌────────────────┐             │
│ Generate Graph │ ⭐ NEW      │
│  (Matplotlib)  │             │
│                │             │
│ Creates:       │             │
│ • Bar Chart    │             │
│ • Line Chart   │             │
│ • Pie Chart    │             │
│ • Scatter Plot │             │
└────────┬───────┘             │
         │                     │
         └─────────┬───────────┘
                   │
                   ▼
        ┌──────────────────┐
        │  Return Results  │
        │                  │
        │ • SQL Query      │
        │ • Text Answer    │
        │ • Graph (if any) │
        └─────────┬────────┘
                  │
                  ▼
        ┌──────────────────┐
        │ Display in UI    │
        │   (Chainlit)     │
        │                  │
        │ Shows:           │
        │ ✓ Question       │
        │ ✓ SQL Query      │
        │ ✓ Text Answer    │
        │ ✓ Graph Image    │
        └──────────────────┘
```

## Decision Logic Detail

```
┌──────────────────────────────────────────────────────────┐
│              DECIDE GRAPH NEED (AI Analysis)             │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Input: Question + Query Results                        │
│                                                          │
│  AI Considers:                                          │
│  ┌────────────────────────────────────────────┐         │
│  │ Question Type Analysis                      │         │
│  │ • "breakdown" → likely needs graph          │         │
│  │ • "trend" → likely needs graph              │         │
│  │ • "distribution" → likely needs graph       │         │
│  │ • "how many" → likely NO graph              │         │
│  │ • "what is" → likely NO graph               │         │
│  └────────────────────────────────────────────┘         │
│                                                          │
│  ┌────────────────────────────────────────────┐         │
│  │ Data Structure Analysis                     │         │
│  │ • Multiple rows → likely needs graph        │         │
│  │ • Single value → likely NO graph            │         │
│  │ • Time series → line chart                  │         │
│  │ • Categories → bar chart                    │         │
│  │ • Percentages → pie chart                   │         │
│  └────────────────────────────────────────────┘         │
│                                                          │
│  Output:                                                 │
│  {                                                       │
│    "needs_graph": true/false,                           │
│    "graph_type": "bar"/"line"/"pie"/"scatter"/"none",   │
│    "reason": "explanation"                              │
│  }                                                       │
└──────────────────────────────────────────────────────────┘
```

## Example Flows

### Flow 1: Simple Count (No Graph)

```
Question: "How many orders were delivered?"
    ↓
Generate SQL: SELECT COUNT(*) FROM orders WHERE order_status='delivered'
    ↓
Execute: Result = 96478
    ↓
Generate Answer: "There were 96,478 orders delivered."
    ↓
Decide Graph: needs_graph=FALSE (single value, no visualization benefit)
    ↓
Display: Text answer only
```

### Flow 2: Yearly Breakdown (With Graph)

```
Question: "Can you give me yearly breakdown of the orders?"
    ↓
Generate SQL: SELECT strftime('%Y', order_purchase_timestamp) as year,
              COUNT(*) as count FROM orders GROUP BY year
    ↓
Execute: Result = [(2016, 329), (2017, 45101), (2018, 54011)]
    ↓
Generate Answer: "Here's the yearly breakdown:
                  2016: 329 orders
                  2017: 45,101 orders
                  2018: 54,011 orders"
    ↓
Decide Graph: needs_graph=TRUE, graph_type="line" (trend over time)
    ↓
Generate Graph: Creates line chart showing growth trend
    ↓
Display: Text answer + Graph image
```

### Flow 3: Top Categories (With Graph)

```
Question: "What are the top 5 product categories?"
    ↓
Generate SQL: SELECT product_category_name, COUNT(*) as count
              FROM products GROUP BY category ORDER BY count DESC LIMIT 5
    ↓
Execute: Result = [(cat1, 1000), (cat2, 800), ...]
    ↓
Generate Answer: "The top 5 categories are: ..."
    ↓
Decide Graph: needs_graph=TRUE, graph_type="bar" (category comparison)
    ↓
Generate Graph: Creates bar chart comparing categories
    ↓
Display: Text answer + Graph image
```

## State Transitions

```
AgentState {
  question: str           // Original user question
  sql_query: str          // Generated SQL
  query_result: str       // JSON results from database
  final_answer: str       // Natural language answer
  error: str              // Any errors encountered
  iteration: int          // Retry counter
  needs_graph: bool       // ⭐ NEW: Should graph be shown?
  graph_type: str         // ⭐ NEW: bar/line/pie/scatter
  graph_image: str        // ⭐ NEW: base64 encoded PNG
}
```

## Conditional Routing

```
After execute_sql:
    if error exists:
        if iteration < 3:
            → handle_error → execute_sql (retry)
        else:
            → generate_answer (give up)
    else:
        → generate_answer

After generate_answer:
    → decide_graph_need

After decide_graph_need:
    if needs_graph == true:
        → generate_graph → END
    else:
        → END (skip graph)
```
