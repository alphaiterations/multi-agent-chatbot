# Quick Start Guide

## Setup in 3 Steps

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Configure API Key
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 3️⃣ Initialize Database
```bash
python db_init.py
```

## Run the Chatbot

```bash
chainlit run app.py
```

The chatbot will open in your browser at `http://localhost:8000`

## Try These Questions

- "How many orders were delivered?"
- "What are the top 5 product categories?"
- "Show me customers from São Paulo"
- "What's the average review score?"
- "Which payment method is most popular?"

## Architecture Overview

```
User Question → LangGraph Agent → SQL Query → Database → Answer
                    ↓
              [OpenAI GPT-4o-mini]
```

**Components:**
- **Frontend**: Chainlit (Web UI)
- **Agent**: LangGraph (Workflow orchestration)
- **AI**: OpenAI GPT-4o-mini (SQL generation & answer formatting)
- **Database**: SQLite (E-commerce data)

## Troubleshooting

**Error: "No module named 'langgraph'"**
→ Run: `pip install -r requirements.txt`

**Error: "Database not found"**
→ Run: `python db_init.py`

**Error: "API key not found"**
→ Create `.env` file with your OpenAI API key

---

For detailed documentation, see [README.md](README.md)
