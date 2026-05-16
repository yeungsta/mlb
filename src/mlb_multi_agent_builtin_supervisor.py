import sys
import os

from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(__file__))

from typing import TypedDict
from typing_extensions import Annotated, Literal

from langgraph.graph import END, START, MessagesState, StateGraph, add_messages
from langchain.messages import SystemMessage, HumanMessage
from langchain_core.messages import AnyMessage
from langgraph.prebuilt import ToolNode
from langgraph_supervisor import create_supervisor
from langchain.agents import create_agent

from llm.get_llm import get_report_writing_llm, get_toolcalling_llm
from tools.misc_tools import current_date
from tools.pybaseball_tools import head_to_head_stats, retrieve_historical_player_id, retrieve_batter_exit_velo_stats, retrieve_pitcher_pitch_type_stats
from tools.statsapi_tools import game_info, retrieve_game_id, starting_lineups

# Initialize the model
llm = get_report_writing_llm()
# llm = get_lightweight_llm()

# create agents
individual_player_agent = create_agent(
    model=llm,
    tools=[current_date, retrieve_historical_player_id, retrieve_pitcher_pitch_type_stats, retrieve_batter_exit_velo_stats],
    name="individual_player_agent",
    system_prompt="You are a provider of individual player stats."
)

head_to_head_agent = create_agent(
    model=llm,
    tools=[current_date, retrieve_historical_player_id, head_to_head_stats],
    name="head_to_head_agent",
    system_prompt="You are provider of historical, head-to-head stats between a pitcher and a batter."
)

game_agent = create_agent(
    model=llm,
    tools=[current_date, retrieve_game_id, game_info, starting_lineups],
    name="game_agent",
    system_prompt="You are a provider of game-specific information."
)

# Create built-in supervisor workflow
workflow = create_supervisor(
    [individual_player_agent, head_to_head_agent, game_agent],
    model=llm,
    prompt=(
        """
        You are a baseball matchup analyzer for:
        1. pitcher vs. batter matchups, in which case you should reference individual stats and historical head-to-head stats.
        2. starting pitchers' matchup for a particular game, in which case you should reference individual stats and game-specific information.
        3. a starting pitcher's matchup to the opposing team's lineup for a particular game, in which case you should reference individual stats, historical head-to-head stats, and game-specific information.
        
        Provide a short report of the matchup analysis based on the retrieved stats. Reference specific stats in your analysis.
        Decide which party has the advantage in the matchup.
        In your report title, include which LLM model and version you're based on, and the time range of the data analyzed.
        """
        # "You are a team supervisor managing a individual player agent, a head-to-head agent, and a game info agent. "
        # "For a given baseball matchup analysis task, you will decide which agent(s) to call based on the conversation history and the results returned from each agent. "
        # "The individual player agent provides individual player stats for a given player and time range. "
        # "The head-to-head agent provides historical, head-to-head stats between a pitcher and a batter. "
        # "The game info agent provides game-specific information, such as the starting pitchers and starting lineups for both teams for a particular game. "
        # "Given the conversation, decide who should act next, or FINISH if the task is complete. Each agent will report back with their result before you decide again."
        )
)

app = workflow.compile()

# Invoke from user input
# messages = [HumanMessage(content="What's today's date?")]
# messages = [HumanMessage(content="Look up Clayton Kershaw's MLBAM ID.")]
# messages = [HumanMessage(content="Head to head stats for Dylan Cease vs. Mookie Betts.")]
# messages = [HumanMessage(content="Clayton Kershaw vs. Mike Trout")]
# messages = [HumanMessage(content="Mike Trout vs. Clayton Kershaw")]
# messages = [HumanMessage(content="Dylan Cease vs. Mookie Betts")]
# messages = [HumanMessage(content="When's the next game for the Dodgers, who are the starting pitchers, and what are the lineups of both teams?")]
# messages = [HumanMessage(content="info on today's Dodgers game")]
# messages = [HumanMessage(content="Analyze today's Dodgers game's starting pitchers.")]
# messages = [HumanMessage(content="Today's Dodgers game's starting pitcher vs. the opposing lineup")]

# state = app.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]
# for m in state["messages"]:
#     m.pretty_print()

# testing individual agents
# query = "Give me starting lineup of today's Dodgers game."
# for step in game_agent.stream(
#     {"messages": [{"role": "user", "content": query}]}
# ):
#     for update in step.values():
#         for message in update.get("messages", []):
#             message.pretty_print()




