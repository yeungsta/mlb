import sys
import os
import datetime

sys.path.insert(0, os.path.dirname(__file__))

from typing import TypedDict
from typing_extensions import Annotated, Literal

from langgraph.graph import END, START, MessagesState, StateGraph, add_messages
from langchain.messages import SystemMessage, HumanMessage
from langchain_core.messages import AnyMessage
from langgraph.prebuilt import ToolNode

from llm.get_llm import get_heavyweight_llm, get_lightweight_llm
from tools.misc_tools import current_date
from tools.pybaseball_tools import head_to_head_stats, player_lookup, retrieve_batter_stats, retrieve_pitcher_stats
from tools.statsapi_tools import game_info, retrieve_game_id, starting_lineups
from models.state import State
from nodes.report_compiler import report_compiler

# Initialize the model
# llm = get_heavyweight_llm()
llm = get_lightweight_llm()

# Augment the LLM with tools
tools = [current_date, player_lookup, retrieve_pitcher_stats, retrieve_batter_stats, head_to_head_stats, retrieve_game_id, game_info, starting_lineups]
llm_with_tools = llm.bind_tools(tools)

# Nodes
tool_caller = ToolNode(tools)

def stat_retrieval(state: State):
    """
    Stat retrieval node that calls only supplied tools based on user input in the messages:
    1. For matchup requests that are date specific, first retrieve the game ID for the specified date and team.
    2. Individual player stats retrieved for the requested time range (default to the past year if no time range is provided)
        a. store retrieved stats in the state under either `pitcher_stats` or `batter_stats` so that they can be referenced in subsequent tool calls and the final analysis
    3. Historical head-to-head data between a pitcher and batter based on their MLBAM IDs, starting with the earliest possible date of their matchup history.
    4. For a starting pitcher's matchup to the opposing team's lineup, 
    retrieve the historical performance of the starting pitcher against each of the opposing team's lineup players, 
    as well as individual stats for the starting pitcher and the opposing team's lineup players.
    Returns tool calls without any extraneous text, questions, summary, or analysis.
    """
    msg = llm_with_tools.invoke(
            [
                SystemMessage(
                    content=
                    """
                    Stat retrieval node that calls only supplied tools based on user input in the messages:
                    1. For matchup requests that are date specific, first retrieve the game ID for the specified date and team.
                    2. Individual player stats retrieved for the requested time range (default to the past year if no time range is provided)
                        a. store retrieved stats in the state under either `pitcher_stats` or `batter_stats` so that they can be referenced in subsequent tool calls and the final analysis
                    3. Historical head-to-head data between a pitcher and batter based on their MLBAM IDs, starting with the earliest possible date of their matchup history.
                    4. For a starting pitcher's matchup to the opposing team's lineup, 
                    retrieve the historical performance of the starting pitcher against each of the opposing team's lineup players, 
                    as well as individual stats for the starting pitcher and the opposing team's lineup players.
                    Returns tool calls without any extraneous text, questions, summary, or analysis.
                    """
                )
            ] + state["messages"]   #must include previous messages in the state to provide context for the LLM
        )
    
    #if the msg is an AIMessage with tool calls, keep a record of the tool call name and ID
    tool_call_records = []
    if msg.tool_calls:
        for tool_call in msg.tool_calls:
            tool_call_records.append({"name": tool_call["name"], "id": tool_call["id"]})

    #if the msg is an AIMessage without tool calls, save the content of the message in the state so that it can be referenced in the final analysis
    # (this allows the LLM to provide additional context or information in the final analysis even if it doesn't require additional tool calls)
    player_stats = []
    if not msg.tool_calls:
        player_stats = msg.content
        
    return {
        "messages": [msg],
        "player_stats": player_stats,
        "llm_model": llm.model
        # "head_to_head_stats": head_to_head_stats,
        # "game_stats": game_stats
    }

def matchup_synthesizer(state: State):
    """
    You are an analyzer in the voice of Vin Scully, tasked with synthesizing a short analysis based on the information below. Reference specific stats in your analysis.
    Decide who has the advantage in the matchup.    
    """

    msg = llm.invoke("You are an analyzer in the voice of Vin Scully, tasked with synthesizing a short analysis based on the information below." +
                     f"Reference specific stats in your analysis. Decide who has the advantage in the matchup: {state["messages"][-1].content}")

    return {
        "summary": msg.content
    }

# Conditional edge function to route to the tool node or end based upon whether the LLM made a tool call
def continue_tool_usage(state: MessagesState) -> str:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls: # pyright: ignore[reportAttributeAccessIssue]
        return "Pass"

    # Otherwise, we stop (reply to the user)
    return "Fail"

# Build workflow
graph = StateGraph(State)

# Add nodes
graph.add_node("stat_retrieval", stat_retrieval)
graph.add_node("tool_caller", tool_caller) # pyright: ignore[reportArgumentType]
graph.add_node("matchup_synthesizer", matchup_synthesizer)
graph.add_node("report_compiler", report_compiler)

# connect nodes
graph.add_edge(START, "stat_retrieval")

#tool loop
graph.add_conditional_edges(
    "stat_retrieval",
    continue_tool_usage,
    { "Pass": "tool_caller", "Fail": "matchup_synthesizer"}
)
graph.add_edge("tool_caller", "stat_retrieval")  #after performing the tool call, we go back to the kickoff node to allow for additional tool calls if necessary (e.g. if the LLM needs to look up additional players or stats)

graph.add_edge("matchup_synthesizer", "report_compiler")

graph.add_edge("report_compiler", END)

workflow = graph.compile()

# Invoke from user input
# messages = [HumanMessage(content="What's today's date?")]
# messages = [HumanMessage(content="Look up Clayton Kershaw's MLBAM ID.")]
# messages = [HumanMessage(content="Head to head stats for Dylan Cease vs. Mookie Betts.")]
# messages = [HumanMessage(content="Clayton Kershaw vs. Mike Trout")]
# messages = [HumanMessage(content="Mike Trout vs. Clayton Kershaw")]
# messages = [HumanMessage(content="Dylan Cease vs. Mookie Betts")]
# messages = [HumanMessage(content="Give me Justin Wrobleski's stats")]
# messages = [HumanMessage(content="When's the next game for the Dodgers, who are the starting pitchers, and what are the lineups of both teams?")]
# messages = [HumanMessage(content="info on today's Dodgers game")]
# messages = [HumanMessage(content="Analyze today's Dodgers game's starting pitchers.")]
# messages = [HumanMessage(content="Look up Kazuma Okamoto's stats.")]
# messages = [HumanMessage(content="Analyze today's Yankees game's matchup between the starting pitchers.")]
# messages = [HumanMessage(content="Analyze today's Dodger's starting pitcher vs. the opposing lineup.")]

# state = workflow.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]
# for m in state["messages"]:
#     m.pretty_print()
# print(state["summary"])

