# mlb
Matchup LLM for Baseball (MLB) Agent

# .env
LANGSMITH_PROJECT="baseball_matchup"
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your key>
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# Add API keys for connecting to LLM providers, data sources, and other integrations here
OLLAMA_API_BASE="http://localhost:11434"
OLLAMA_API_KEY=<your key>

# run via LangSmith UI
langgraph dev

# run pytest
tests/integration_tests/test_mlb.py
