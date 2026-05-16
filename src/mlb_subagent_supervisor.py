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
from langchain.tools import tool

from llm.get_llm import get_report_writing_llm, get_toolcalling_llm
from tools.misc_tools import current_date
from tools.pybaseball_tools import head_to_head_stats, retrieve_historical_player_id, retrieve_batter_exit_velo_stats, retrieve_pitcher_pitch_type_stats
from tools.statsapi_tools import game_info, retrieve_game_id, starting_lineups

import warnings

# Suppress the Python 3.13 threading cleanup warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Initialize the model
llm = get_report_writing_llm()
# llm = get_lightweight_llm()

# subagents
# TODO: try breaking this into a batter and a pither stat subagent
individual_player_subagent = create_agent(
    model=llm,
    tools=[current_date, retrieve_historical_player_id, retrieve_pitcher_pitch_type_stats, retrieve_batter_exit_velo_stats],
    name="individual_player_subagent",
    system_prompt="You are a provider of individual player stats."
)

head_to_head_subagent = create_agent(
    model=llm,
    tools=[current_date, retrieve_historical_player_id, head_to_head_stats],
    name="head_to_head_subagent",
    system_prompt="You are provider of historical, head-to-head stats between a pitcher and a batter."
)

game_subagent = create_agent(
    model=llm,
    tools=[current_date, retrieve_game_id, game_info, starting_lineups],
    name="game_subagent",
    system_prompt="You are a provider of game-specific information."
)

# wrap subagents as tools for supervisor agent to call
@tool
def retrieve_individual_player_stats(request: str) -> str:
    """
    Provides individual stats for a player using natural language.

    Use this when the user wants to retrieve individual player stats 
    for the requested time range (or default to the past year if no time range is provided).

    Input: Natural language stats request for an individual player (e.g., "What are Mike Trout's stats for the 2023 season?")
    """
    result = individual_player_subagent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

@tool
def retrieve_head_to_head_stats(request: str) -> str:
    """
    Provides historical, head-to-head stats between a pitcher and a batter.

    Use this when the user wants to retrieve head-to-head stats between a specific pitcher and batter.

    Input: Natural language stats request for a head-to-head matchup (e.g., "What are Clayton Kershaw's stats against Mike Trout?")
    """
    result = head_to_head_subagent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

@tool
def retrieve_game_info(request: str) -> str:
    """
    Provides game-specific information.

    Use this when the user wants to retrieve information about a particular game, such as the starting pitchers
    and starting lineups for both teams, date and time of the game, and current status of the game.

    Input: Natural language info request for a game (e.g., "What are the starting pitchers for the Yankees vs. Red Sox game today?")
    """
    result = game_subagent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

# supervisor agent
supervisor_agent = create_agent(
    model=llm,
    tools=[retrieve_individual_player_stats, retrieve_head_to_head_stats, retrieve_game_info],
    system_prompt=(
        """
        You are a baseball matchup analyzer for:
        1. pitcher vs. batter matchups, in which case you should reference individual stats and historical head-to-head stats.
        2. starting pitchers' matchup for a particular game, in which case you should reference individual stats and game-specific information.
        3. a starting pitcher's matchup to the opposing team's lineup for a particular game, in which case you should reference individual stats, historical head-to-head stats, and game-specific information.
        
        Provide a short report of the matchup analysis based on the retrieved stats. Reference specific stats in your analysis.
        Decide which party has the advantage in the matchup.
        In your report title, include which LLM model and version you're based on, and the time range of the data analyzed.
        """
        )
)

# Invoke from user input
# messages = [HumanMessage(content="What's today's date?")]
# messages = [HumanMessage(content="Look up Clayton Kershaw's MLBAM ID.")]
# messages = [HumanMessage(content="Head to head stats for Dylan Cease vs. Mookie Betts.")]
# messages = [HumanMessage(content="Clayton Kershaw vs. Mike Trout")]
# messages = [HumanMessage(content="Mike Trout vs. Clayton Kershaw")]
# messages = [HumanMessage(content="Dylan Cease vs. Mookie Betts")]
# messages = [HumanMessage(content="When's the next game for the Dodgers, who are the starting pitchers, and what are the lineups of both teams?")]
# messages = [HumanMessage(content="info on today's Dodgers game")]
# messages = [HumanMessage(content="Today's Dodgers game's starting pitcher vs. the opposing lineup")]
# messages = [HumanMessage(content="Today's Yankees's starting pitcher vs. the opposing lineup")]
# messages = [HumanMessage(content="Analyze today's Yankees game's starting pitchers matchup")]

# state = supervisor_agent.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]
# for m in state["messages"]:
#     m.pretty_print()

# graph = StateGraph(State)

# # Add nodes
# graph.add_node("matchup_synthesizer", matchup_synthesizer)

# graph.add_node("individual_player_agent", individual_player_agent)
# graph.add_node("individual_player_tool_caller", individual_player_tool_caller)

# graph.add_node("head_to_head_agent", head_to_head_agent)
# graph.add_node("head_to_head_tool_caller", head_to_head_tool_caller) 

# graph.add_node("game_agent", game_agent)
# graph.add_node("game_info_tool_caller", game_info_tool_caller)

# # Add edges to connect nodes
# graph.add_edge(START, "matchup_synthesizer")

# graph.add_conditional_edges(
#     "matchup_synthesizer",
#     lambda x: x["next"],
#     {"individual_player_agent": "individual_player_agent", 
#      "head_to_head_agent": "head_to_head_agent", 
#      "game_agent": "game_agent", 
#      "FINISH": END}
# )
    
# #tool loops
# graph.add_conditional_edges(
#     "individual_player_agent",
#     continue_tool_usage,
#     { "Pass": "individual_player_tool_caller", "Fail": "matchup_synthesizer" }
# )
# graph.add_edge("individual_player_tool_caller", "individual_player_agent")  

# graph.add_conditional_edges(
#     "head_to_head_agent",
#     continue_tool_usage,
#     { "Pass": "head_to_head_tool_caller", "Fail": "matchup_synthesizer" }
# )
# graph.add_edge("head_to_head_tool_caller", "head_to_head_agent")

# graph.add_conditional_edges(
#     "game_agent",
#     continue_tool_usage,
#     { "Pass": "game_info_tool_caller", "Fail": "matchup_synthesizer" }
# )
# graph.add_edge("game_info_tool_caller", "game_agent")

# graph.add_edge("matchup_synthesizer", END)
# workflow = graph.compile()




