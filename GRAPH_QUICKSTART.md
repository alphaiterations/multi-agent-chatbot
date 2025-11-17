# Quick Start Guide: Graph Agent Feature

## What's New?

Your Text2SQL chatbot now automatically generates visualizations when they would be helpful! 🎉

## How to Use

### 1. Start the Chatbot

```bash
chainlit run app.py
```

### 2. Ask Questions Naturally

The chatbot will automatically decide if a graph would help answer your question.

### Questions That Will Show Graphs

✅ **"Can you give me yearly breakdown of the orders?"**
- Shows a line/bar chart of orders by year

✅ **"What are the top 10 product categories by sales?"**
- Shows a bar chart comparing categories

✅ **"Show me the distribution of order statuses"**
- Shows a pie chart of status proportions

✅ **"What's the monthly trend of orders in 2018?"**
- Shows a line chart of monthly trends

### Questions That Won't Show Graphs

❌ **"How many orders were there in 2018?"**
- Simple count - just shows the number

❌ **"What's the average order value?"**
- Single value - no visualization needed

## Example Conversation

**You:** "Can you give me yearly breakdown of the orders?"

**Bot Response:**
```
Your Question: Can you give me yearly breakdown of the orders?

Generated SQL Query:
SELECT strftime('%Y', order_purchase_timestamp) as year, 
       COUNT(*) as order_count
FROM orders
GROUP BY year
ORDER BY year

Answer:
Based on the query results, here's the yearly breakdown of orders:
- 2016: 329 orders
- 2017: 45,101 orders  
- 2018: 54,011 orders

There's a significant growth trend, with orders increasing substantially 
from 2016 to 2018.
```

**[A line chart or bar chart automatically appears showing the trend]**

## Testing the Feature

Test both scenarios:

```bash
# Run the test script
python text2sql_agent.py
```

This will show:
1. A simple query without graph
2. A breakdown query with graph

## What Happens Behind the Scenes

```
User Question
     ↓
Generate SQL Query
     ↓
Execute Query
     ↓
Generate Text Answer
     ↓
🤖 AI Decides: "Would a graph help here?"
     ↓
     ├─ YES → Generate appropriate chart (bar/line/pie/scatter)
     └─ NO → Just show text answer
     ↓
Display to User
```

## Customization

Want to adjust when graphs appear? Edit `text2sql_agent.py`:

```python
# In decide_graph_need() function
# Modify the decision criteria in the prompt
```

## Features

🎯 **Smart Detection** - Automatically knows when graphs add value
📊 **Multiple Chart Types** - Bar, line, pie, and scatter plots
🎨 **Professional Styling** - Clean, readable visualizations  
⚡ **Seamless Integration** - No extra commands needed

## Tips

1. **Be specific about "breakdown"** - Words like "breakdown", "trend", "distribution" signal that a graph would be helpful

2. **Ask for comparisons** - "Compare", "top 10", "by category" questions often get graphs

3. **Time-based queries** - "Monthly", "yearly", "over time" questions usually get line charts

4. **Proportions** - "Distribution", "percentage", "share" questions often get pie charts

## Troubleshooting

**Graph not showing?**
- Make sure you have the latest requirements: `pip install -r requirements.txt`
- Check that your OpenAI API key is set

**Wrong graph type?**
- The AI learns what works best, but you can adjust the prompts in the code

**Want to force a specific graph?**
- Currently automatic only, but you can modify the code to accept user preferences

## Next Steps

Try these example questions:
- "Show me the top 5 states by number of customers"
- "What's the trend of reviews over time?"
- "Compare payment methods by usage"
- "Show me order volume by month in 2017"

Enjoy your enhanced chatbot! 🚀
