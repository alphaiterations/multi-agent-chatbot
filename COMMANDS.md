# Commands Cheatsheet

## Setup Commands

```bash
# Install all dependencies
pip install -r requirements.txt

# Create environment file from template
cp .env.example .env

# Initialize the database (creates ecommerce.db)
python db_init.py

# Verify setup is correct
python test_setup.py
```

## Running the Application

```bash
# Start the chatbot (opens in browser at http://localhost:8000)
chainlit run app.py

# Run in debug mode
chainlit run app.py --debug

# Run on custom port
chainlit run app.py --port 8080
```

## Testing

```bash
# Test the agent directly (without UI)
python text2sql_agent.py

# Verify complete setup
python test_setup.py
```

## Database Management

```bash
# Recreate database from scratch
python db_init.py

# Check database tables (SQLite CLI)
sqlite3 ecommerce.db ".tables"

# View table schema
sqlite3 ecommerce.db ".schema customers"

# Run SQL query directly
sqlite3 ecommerce.db "SELECT COUNT(*) FROM orders;"
```

## Development

```bash
# Install in development mode
pip install -e .

# Update dependencies
pip install -r requirements.txt --upgrade

# Check for package updates
pip list --outdated
```

## Environment Variables

```bash
# View current environment variables
cat .env

# Edit environment variables
nano .env  # or use your preferred editor

# Required variables:
# OPENAI_API_KEY=sk-your-key-here
```

## Git Commands (if using version control)

```bash
# Check status
git status

# Add new files (respects .gitignore)
git add .

# Commit changes
git commit -m "Add text2SQL chatbot"

# Push to remote
git push origin main
```

## Troubleshooting Commands

```bash
# Check Python version
python --version  # Should be 3.8+

# Check if packages are installed
pip list | grep langgraph
pip list | grep chainlit
pip list | grep openai

# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

## Useful SQLite Queries for Testing

```bash
# Open SQLite interactive shell
sqlite3 ecommerce.db

# Then run these queries:
.tables                                    # List all tables
.schema orders                             # Show table structure
SELECT COUNT(*) FROM customers;            # Count customers
SELECT * FROM orders LIMIT 5;              # View sample orders
SELECT order_status, COUNT(*) FROM orders GROUP BY order_status;  # Order stats
.quit                                      # Exit SQLite
```

## Port Management (if port 8000 is busy)

```bash
# Find process using port 8000
lsof -i :8000

# Kill process on port 8000 (use PID from above)
kill -9 <PID>

# Or run Chainlit on different port
chainlit run app.py --port 8080
```

## Quick Reference

| Task | Command |
|------|---------|
| Setup | `pip install -r requirements.txt` |
| Config | `cp .env.example .env` |
| Init DB | `python db_init.py` |
| Test | `python test_setup.py` |
| Run | `chainlit run app.py` |
| Debug | `chainlit run app.py --debug` |

---

**Pro Tip**: Create an alias in your `~/.zshrc` or `~/.bashrc`:
```bash
alias chatbot="cd /Users/vijendra/multi-agent-chatbot && chainlit run app.py"
```

Then just run: `chatbot`
