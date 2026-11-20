# ⚾ Matchup LLM for Baseball

**Turn a baseball question into a scouting report backed by MLB Stats API and Statcast data.** Vin AI is a Python and LangGraph agent that looks up players and games, compares pitchers with hitters, and writes HTML reports in a Vin Scully-inspired voice.

[Quick start](#quick-start) · [Example prompts](#example-prompts) · [Python example](#run-from-python) · [Codebase map](#codebase-map) · [Tests](#tests)

## What you can analyze

| Feature | What the agent looks up |
| --- | --- |
| Pitcher scouting | Current-season pitching totals and trailing-year Statcast pitch-type metrics |
| Hitter scouting | Current-season batting totals and trailing-year Statcast exit-velocity metrics |
| Batter vs. pitcher | Historical head-to-head Statcast data, using MLBAM IDs resolved from player names |
| Starting pitcher vs. a lineup | The game, opposing batting order, individual player stats, and historical matchups against lineup hitters |
| Game lookup | Scheduled start time, game status, probable starters, and published lineups for a team and date |
| Matchup reports | A retrieved-stat summary, narrative analysis, and generated title, rendered to HTML with Jinja2 |

Probable starters and lineups depend on what MLB has published for the game. Historical comparisons depend on available Statcast data.

## Quick start

You'll need [uv](https://docs.astral.sh/uv/), Python 3.13 or later, and a model that supports tool calling. The default setup uses a local [Ollama](https://ollama.com/) server and the `gpt-oss:120b-cloud` model. The cloud model requires an authenticated Ollama account.

```bash
git clone https://github.com/yeungsta/mlb.git
cd mlb
uv sync --locked
ollama signin
ollama pull gpt-oss:120b-cloud
```

On Linux, building the `simpleaudio` development dependency requires a C compiler, Python development headers, and ALSA development headers. For a text-only setup, use `uv sync --locked --no-install-package simpleaudio` and add `--no-sync` after `uv run` in the commands below. If your home directory is read-only, set `PYBASEBALL_CACHE` to a writable directory before starting the graph.

Start Ollama with `ollama serve` in a separate terminal if the server is down. For a different Ollama model, update `OLLAMA_MODEL` in [the model configuration](src/llm/get_llm.py) and pull that model. The same module has an OpenRouter option (`USE_OLLAMA = False`, with `OPENROUTER_API_KEY`) and experimental Gemini helpers.

Create a `.env` file in the repository root. For optional LangSmith tracing, add the following and replace the placeholder with your key.

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=baseball_matchup
LANGSMITH_API_KEY=your-langsmith-key
```

> [!IMPORTANT]
> Generating a report saves an HTML file and attempts Gmail SMTP delivery to the recipient configured in the [report compiler](src/nodes/report_compiler.py). Review that code before running the graph or integration tests. Disable the SMTP block for local-only runs.

Start the development server and open the Studio URL printed in the terminal. Choose **vin-ai** and enter a prompt in the graph's `messages` input.

```bash
uv run langgraph dev --allow-blocking
```

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

From the repository root, invoke the same graph directly. The example uses the default local Ollama connection.

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

[MIT](LICENSE)
