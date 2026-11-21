# ⚾ Matchup LLM for Baseball

**Turn a baseball question into a scouting report backed by MLB Stats API and Statcast data.** Vin AI is a Python and LangGraph agent that looks up players and games, compares pitchers with hitters, and writes HTML reports in a Vin Scully-inspired voice.

[Quick start](#quick-start) · [Chat playground](#chat-playground) · [Example prompts](#example-prompts) · [Python example](#run-from-python) · [Codebase map](#codebase-map) · [Tests](#tests)

## What you can analyze

| Feature | What the agent looks up |
| --- | --- |
| Pitcher scouting | Current-season pitching totals and trailing-year Statcast pitch-type metrics |
| Hitter scouting | Current-season batting totals, trailing-year Statcast exit velocity, and season wOBA and xwOBA |
| Batter vs. pitcher | Historical head-to-head Statcast data, using MLBAM IDs resolved from player names |
| Starting pitcher vs. a lineup | The game, opposing batting order, individual player stats, and historical matchups against lineup hitters |
| Game lookup | Scheduled start time, game status, probable starters, and published lineups for a team and date |
| Matchup reports | A retrieved-stat summary, narrative analysis, and generated title, rendered to HTML with Jinja2 |

Probable starters and lineups depend on what MLB has published for the game. Historical comparisons depend on available Statcast data.

## Quick start

You'll need [uv](https://docs.astral.sh/uv/), Python 3.13 or later, and a model that supports tool calling. The default model provider is OpenRouter.

```bash
git clone https://github.com/yeungsta/mlb.git
cd mlb
uv sync --locked
```

On Linux, building the `simpleaudio` development dependency requires a C compiler, Python development headers, and ALSA development headers. For a text-only setup, use `uv sync --locked --no-install-package simpleaudio` and add `--no-sync` after `uv run` in the commands below. If your home directory is read-only, set `PYBASEBALL_CACHE` to a writable directory before starting the graph.

Create a `.env` file in the repository root and set `OPENROUTER_API_KEY`. For optional LangSmith tracing, set `LANGSMITH_TRACING=true`, `LANGSMITH_PROJECT=baseball_matchup`, and `LANGSMITH_API_KEY`. To use [Ollama](https://ollama.com/), set `USE_OLLAMA = True` in [the model configuration](src/llm/get_llm.py) and start Ollama with the configured model.

Start the development server. You can open the Studio URL printed in the terminal, choose **vin-ai**, and enter a prompt in `messages`.

```bash
uv run langgraph dev --allow-blocking --no-browser
```

## Chat playground

With LangGraph running on port 2024, start the frontend from a second terminal. It requires Node.js 20.19+ or 22.12+.

```bash
cd web
npm ci
npm run dev
```

Open [localhost:5173](http://localhost:5173). Pick an example to fill the composer, edit it, then send it. The chat shows live progress, the finished analysis, retrieved stats, and the tool calls from each run. Follow-ups use the current LangGraph thread. **New chat** starts a fresh thread.

HTML reports continue to be saved locally. To enable Gmail delivery, set `VIN_AI_EMAIL_ENABLED=1`, `VIN_AI_SMTP_SENDER`, `VIN_AI_SMTP_APP_PASSWORD`, and `VIN_AI_SMTP_RECIPIENT` in the backend environment.

### Example prompts

| Try this prompt | Workflow |
| --- | --- |
| “Analyze Trevor Megill’s pitching this season and summarize his pitch mix.” | Pitcher scouting |
| “Analyze Tommy Edman’s batting and recent exit velocity.” | Hitter scouting |
| “Compare Mike Trout and Clayton Kershaw in their historical head-to-head matchups.” | Batter vs. pitcher |
| “Analyze the Dodgers’ starting pitcher against the Yankees’ lineup on October 25, 2024.” | Pitcher vs. lineup |
| “Who started the October 25, 2024 Dodgers game, and what were both batting orders?” | Game lookup |

Completed reports are saved under `reports/MM-DD-YYYY/<title>.html`. Open the file in a browser to read the narrative and retrieved-stat summary.

## Run from Python

From the repository root, invoke the same graph directly. Set the configured model provider’s credentials in the Python process environment before invoking the graph.

```bash
uv run python - <<'PY'
from langchain.messages import HumanMessage
from src.mlb_single_agent_retriever import build_graph

result = build_graph().invoke({
    "messages": [
        HumanMessage(content="Compare Mike Trout vs. Clayton Kershaw historically.")
    ]
})
print(result["title"])
print(result["summary"])
PY
```

## Codebase map

The main graph loops between the model and its data tools until it has a stats summary. It then writes the analysis, generates a title, and compiles the HTML report.

| Path | Role |
| --- | --- |
| [src/mlb_single_agent_retriever.py](src/mlb_single_agent_retriever.py) | Main `vin-ai` graph and `build_graph()` entry point |
| [src/tools/](src/tools/) | MLB Stats API lookups, pybaseball/Statcast stats, and a current-date tool |
| [src/llm/get_llm.py](src/llm/get_llm.py) | Model factories and settings for tool calling and report writing |
| [src/models/state.py](src/models/state.py) | Graph state and structured report and research models |
| [src/nodes/report_compiler.py](src/nodes/report_compiler.py) · [src/templates/](src/templates/) | Markdown-to-HTML rendering, report layout, and local output |
| [web/](web/) | Chat playground and local proxy to the LangGraph API |
| [src/api/](src/api/) | Schedule helpers and a standalone Statcast analysis script |
| [src/examples/](src/examples/) | Small LangGraph demos for arithmetic tool calls, parallel fan-out and fan-in, and a minimal model call |
| [langgraph.json](langgraph.json) · [langgraph.json.dev](langgraph.json.dev) · [Dockerfile](Dockerfile) | Default graph registration, experimental graph registration, and a Python 3.13 LangGraph container definition |
| [tests/](tests/) · [Makefile](Makefile) | End-to-end matchup checks, scaffolded unit tests, and development commands |

### Experimental graphs

```bash
uv run langgraph dev --allow-blocking --config langgraph.json.dev
```

The dev config registers the main retriever alongside two supervisor designs and the tool-calling and parallelization demos.

- [Subagent supervisor](src/mlb_subagent_supervisor.py) delegates to specialized player, head-to-head, and game agents exposed as tools.
- [Built-in supervisor](src/mlb_multi_agent_builtin_supervisor.py) uses `langgraph-supervisor` to coordinate specialized agents.
- [Multi-agent retrievers](src/mlb_multi_agent_retrievers.py) explores explicit graph routing between specialists as a standalone experiment.

## Tests

Run one of the end-to-end checks from the repository root.

```bash
uv run python -m pytest tests/integration_tests/test_mlb.py -k head_to_head_analysis
```

These tests call the model and live baseball data sources. Speech playback is enabled by default in [test_mlb.py](tests/integration_tests/test_mlb.py). For a text-only run, set `SPEECH_PLAYBACK_ENABLED = False` locally. Playback requires an OpenAI-compatible Ollama speech endpoint that serves `phonon`, configured through `OLLAMA_API_V1_BASE` and `OLLAMA_API_KEY`, plus a working audio device.

## License

# run pytest
tests/integration_tests/test_mlb.py

## Advanced hitting stats

Ask Vin for a batter's weighted on-base average (wOBA) and expected wOBA
(xwOBA), for example, “What were Shohei Ohtani's wOBA and xwOBA in 2025?”

`retrieve_advanced_hitting_stats` takes an MLBAM player ID and a season.
It returns Baseball Savant's regular-season wOBA, xwOBA, and plate appearances
for seasons from 2015 onward. Active-season figures are season to date. In a
matchup report, these figures describe the batter's overall season performance.
[MIT](LICENSE)
