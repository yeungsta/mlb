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

## Advanced hitting stats

Ask Vin for a batter's weighted on-base average (wOBA) and expected wOBA
(xwOBA), for example, “What were Shohei Ohtani's wOBA and xwOBA in 2025?”

`retrieve_advanced_hitting_stats` takes an MLBAM player ID and a season.
It returns Baseball Savant's regular-season wOBA, xwOBA, and plate appearances
for seasons from 2015 onward. Active-season figures are season to date. In a
matchup report, these figures describe the batter's overall season performance.
