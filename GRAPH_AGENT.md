# Graph Agent Documentation

## Overview

The multi-agent chatbot now includes an intelligent **Graph Agent** that automatically determines when visualizations would be helpful and generates appropriate charts to enhance the user experience.

## How It Works

### Agent Workflow

The enhanced LangGraph workflow now includes these additional steps:

1. **Generate SQL** - Converts natural language to SQL query
2. **Execute SQL** - Runs the query against the database
3. **Generate Answer** - Creates a natural language response
4. **Decide Graph Need** ⭐ NEW - AI determines if visualization would be helpful
5. **Generate Graph** ⭐ NEW - Creates appropriate chart if needed

### Graph Decision Logic

The `decide_graph_need` agent analyzes:
- The user's question
- The query results
- The data structure and patterns

It then decides:
- **Should a graph be shown?** (YES/NO)
- **What type of graph?** (bar, line, pie, scatter)

### Supported Graph Types

| Graph Type | Use Case | Example Question |
|-----------|----------|------------------|
| **Bar Chart** | Comparing categories | "Top 10 product categories by sales" |
| **Line Chart** | Trends over time | "Monthly order trends in 2018" |
| **Pie Chart** | Proportions/percentages | "Order status distribution" |
| **Scatter Plot** | Correlations | "Price vs. freight cost relationship" |

## Examples

### Example 1: No Graph Required
**Question:** "How many orders were there in 2018?"

**Response:** 
- ✅ Text answer: "There were 45,101 orders in 2018."
- ❌ No graph (simple count doesn't benefit from visualization)

### Example 2: Bar Chart
**Question:** "What are the top 5 product categories by number of orders?"

**Response:**
- ✅ Text answer with details
- ✅ Bar chart showing category comparisons

### Example 3: Line Chart
**Question:** "Can you give me yearly breakdown of the orders?"

**Response:**
- ✅ Text answer with yearly totals
- ✅ Line chart showing trend over time

### Example 4: Pie Chart
**Question:** "Show me the distribution of payment types"

**Response:**
- ✅ Text answer with percentages
- ✅ Pie chart showing proportions

## Technical Implementation

### State Management

The `AgentState` now includes:
```python
class AgentState(TypedDict):
    question: str
    sql_query: str
    query_result: str
    final_answer: str
    error: str
    iteration: int
    needs_graph: bool      # ⭐ NEW
    graph_type: str        # ⭐ NEW  
    graph_image: str       # ⭐ NEW (base64 encoded)
```

### New Agent Functions

1. **`decide_graph_need(state)`** - Uses GPT-4o-mini to analyze if graph is needed
2. **`generate_graph(state)`** - Creates matplotlib visualization
3. **`should_generate_graph(state)`** - Router function for conditional edges

### Dependencies

Added to `requirements.txt`:
- `matplotlib>=3.5.0` - For chart generation
- `seaborn>=0.12.0` - For better styling

### Chainlit Integration

The `app.py` now:
1. Receives graph data from the agent
2. Decodes base64 image
3. Displays using `cl.Image` element
4. Shows inline with the text response

## Customization

### Adjusting Graph Appearance

Edit `generate_graph()` in `text2sql_agent.py`:

```python
plt.figure(figsize=(10, 6))  # Change size
plt.style.use('seaborn-v0_8-darkgrid')  # Change style
```

### Modifying Decision Logic

Edit the prompt in `decide_graph_need()` to adjust when graphs are shown:

```python
Consider:
- Trends over time → line chart
- Comparisons between categories → bar chart
- Proportions/percentages → pie chart
- Correlations → scatter plot
- Simple counts or single values → NO graph needed
```

### Data Limits

- Bar/Line charts: Limited to top 20 items for readability
- Pie charts: Limited to top 10 slices
- All results: Limited to 100 rows for processing

## Benefits

✅ **Automatic Intelligence** - No need to explicitly request graphs
✅ **Context-Aware** - Only shows graphs when they add value
✅ **Multiple Chart Types** - Selects the most appropriate visualization
✅ **Seamless Integration** - Works within existing workflow
✅ **Enhanced UX** - Visual + text answers for better comprehension

## Installation

Install new dependencies:
```bash
pip install -r requirements.txt
```

## Testing

Test with these example questions:

```python
# Should generate BAR chart
"What are the top 10 cities by number of customers?"

# Should generate LINE chart  
"Show me monthly order trends for 2017"

# Should generate PIE chart
"What's the breakdown of order statuses?"

# Should NOT generate graph
"How many total orders are there?"
```

## Troubleshooting

### Graph not appearing?
- Check that matplotlib and seaborn are installed
- Verify OpenAI API key is set (needed for decision logic)
- Check browser console for errors

### Wrong graph type selected?
- The AI decision can be adjusted via the prompt in `decide_graph_need()`
- You can also force a specific graph type by modifying the logic

### Graph quality issues?
- Adjust DPI: `plt.savefig(buffer, format='png', dpi=150)`
- Change figure size: `plt.figure(figsize=(12, 8))`
- Modify colors and styles in `generate_graph()`
