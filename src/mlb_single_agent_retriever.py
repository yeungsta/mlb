import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from typing import TypedDict
from typing_extensions import Annotated, Literal

from langgraph.graph import END, START, MessagesState, StateGraph, add_messages
from langchain.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.messages import AnyMessage
from langgraph.prebuilt import ToolNode
from langgraph.types import StreamWriter
from langgraph.config import get_stream_writer

from llm.get_llm import get_report_writing_llm, get_toolcalling_llm
from tools.misc_tools import current_date
from tools.pybaseball_tools import head_to_head_stats, retrieve_historical_player_id, retrieve_batter_exit_velo_stats_past_year, retrieve_pitcher_pitch_type_stats_past_year
from tools.statsapi_tools import retrieve_current_player_id, game_info, retrieve_game_id, retrieve_season_hitting_stats, retrieve_season_pitching_stats, starting_lineups
from models.state import MatchupSynthesis, State
from nodes.report_compiler import report_compiler


tool_calling_llm = get_toolcalling_llm()
report_writing_llm = get_report_writing_llm()

simple_llm_model = tool_calling_llm.model.split(":")[0]
combined_llm_models = tool_calling_llm.model.split(":")[0]+":"+str(tool_calling_llm.temperature) + "+" + report_writing_llm.model.split(":")[0]+":"+str(report_writing_llm.temperature)# for both tool calling and report writing (not as good at tool calling as the dedicated tool-calling LLM, but better at report writing than the lightweight LLM, so using it as a middle ground for the stat retrieval node which requires both capabilities)


# initialize tool-calling LLM and bind tools
tools = [current_date, retrieve_current_player_id, retrieve_historical_player_id, 
         retrieve_pitcher_pitch_type_stats_past_year, retrieve_season_pitching_stats, 
         retrieve_batter_exit_velo_stats_past_year, retrieve_season_hitting_stats, 
         head_to_head_stats, retrieve_game_id, game_info, starting_lineups]
llm_with_tools = tool_calling_llm.bind_tools(tools)

# matchup synthesizer LLM w/ structured output
# matchup_synthesizer_llm = report_writing_llm.with_structured_output(MatchupSynthesis
#                                                                     # method="json_mode"
#                                                                     # include_raw=True
#                                                                     )

# Nodes
tool_caller = ToolNode(tools)

def stat_retrieval(state: State):
    writer = get_stream_writer()
    writer({"type": "log", "message": "Retrieving stats...", "progress": 0.1})

    """
    Stat retrieval node that calls only supplied tools based on user input in the messages:
    1. For matchup requests that are date specific, first retrieve the current date, then the game ID for the specified date and team.
    2. Always retrieve pitcher pitch-type stats and batter exit velocity stats for the requested time range (default to the past year if no time range is provided).
    3. Always retrieve current season stats for players.
    4. Historical head-to-head data between a pitcher and batter based on their MLBAM IDs, starting with the earliest possible date of their matchup history.
    5. For a starting pitcher's matchup to the opposing team's lineup, retrieve the historical performance of the starting pitcher against each of the opposing team's lineup players, 
    as well as individual stats for the starting pitcher and the opposing team's lineup players.
    Make the final message a summary of all retrieved stats. Do not ask questions.
    """
    msg = llm_with_tools.invoke(
            [
                SystemMessage(
                    content=
                    """
                    Stat retrieval node that calls only supplied tools based on user input in the messages:
                    1. For matchup requests that are date specific, first retrieve the current date, then the game ID for the specified date and team.
                    2. Always retrieve pitcher pitch-type stats and batter exit velocity stats for the requested time range (default to the past year if no time range is provided).
                    3. Always retrieve current season stats for players.
                    4. Historical head-to-head data between a pitcher and batter based on their MLBAM IDs, starting with the earliest possible date of their matchup history.
                    5. For a starting pitcher's matchup to the opposing team's lineup, retrieve the historical performance of the starting pitcher against each of the opposing team's lineup players, 
                    as well as individual stats for the starting pitcher and the opposing team's lineup players.
                    Make the final message a summary of all retrieved stats. Do not ask questions.
                    """
                )
            ] + state["messages"]   #must include previous messages in the state to provide context for the LLM
        )
    
    #if the msg is an AIMessage with tool calls, keep a record of the tool call name and ID
    # tool_call_records = []
    # if msg.tool_calls:
    #     for tool_call in msg.tool_calls:
    #         tool_call_records.append({"name": tool_call["name"], "id": tool_call["id"]})

    #if the msg is an AIMessage without tool calls, save the content of the message in the state so that it can be referenced in the final analysis
    # (this allows the LLM to provide additional context or information in the final analysis even if it doesn't require additional tool calls)
    # TODO: right now this is just the final stats summary of the stat_retrieval node, not ALL retrieved stats.
    stats_summary = ""
    if not msg.tool_calls:
        stats_summary = msg.content

    return {
        "messages": [msg],
        "stats_summary": stats_summary,
        # "llm_model": combined_llm_models,
        "llm_model": simple_llm_model
    }

def matchup_synthesizer(state: State):
    writer = get_stream_writer()
    writer({"type": "log", "message": "Vin synthesizing a matchup analysis...", "progress": 0.5})

    """
    You are an analyzer in the voice of Vin Scully, tasked with synthesizing an analysis based on {state["stats_summary"]} and game info from {game_stats}.
    Reference specific stats in your analysis. Decide who has the advantage in the matchup. Do not include a the prologue or setting.
    """

    if not state["stats_summary"] or len(state["stats_summary"]) < 10:
        print("No stats summary was summarized, skipping synthesis!")

        # # 1. Calculate the actual tokens consumed by the current history    
        # current_tokens = tool_calling_llm.get_num_tokens_from_messages(list(state["messages"]))
        
        # # 2. Reference your target model's total context limit
        # # (e.g., 128,000 for gpt-4o)
        # max_context = 128000 
        
        # usage_percentage = (current_tokens / max_context) * 100
        # print(f"Context Window Usage: {current_tokens}/{max_context} tokens ({usage_percentage:.2f}%)")
        
        return {
            "summary": ""
        }
    
    #save off game info for part of summary analysis
    game_stats = ""
    for msg in state["messages"]:
        if msg.name == "game_info":
            game_stats = msg.content

    synthesis = report_writing_llm.invoke(
        f"""
        You are an analyzer in the voice of Vin Scully, tasked with synthesizing an analysis based on the following data:

        Stats Summary:
        {state["stats_summary"]}

        Game Info:
        {game_stats}

        Reference specific stats in your summary. Decide who has the advantage in the matchup. 
        Do not include a prologue or setting.
        """
    )
    
    return {
        # "title": synthesis.title,
        # "summary": synthesis.summary
        "summary": synthesis.content
    }

def title_maker(state: State):
    writer = get_stream_writer()
    writer({"type": "log", "message": "Coming up with a title...", "progress": 0.9})

    """
    You are title maker that comes up with one, catchy and dramatic title for this report: {state["summary"]}. Just give me the title, do not include any additional text.
    """

    if not state["summary"]:
        return {
            "title": ""
        }
    
    title = report_writing_llm.invoke(
        f"""
        You are title maker that comes up with one, catchy and dramatic title for this report: {state["summary"]}. Just give me the title, do not include any additional text.
        """
    )
    
    return {
        "title": title.content,
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

def build_graph():
    # Build workflow
    graph = StateGraph(State)

    # Add nodes
    graph.add_node("stat_retrieval", stat_retrieval)
    graph.add_node("tool_caller", tool_caller) # pyright: ignore[reportArgumentType]
    graph.add_node("matchup_synthesizer", matchup_synthesizer)
    graph.add_node("title_maker", title_maker)
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

    graph.add_edge("matchup_synthesizer", "title_maker")

    graph.add_edge("title_maker", "report_compiler")

    graph.add_edge("report_compiler", END)

    return graph.compile()

# Invoke from user input
# messages = [HumanMessage(content="Analyze Alex Vesia's stats")]
# state = build_graph().invoke({"messages": messages}) # pyright: ignore[reportArgumentType]
# for m in state["messages"]:
#     m.pretty_print()
# print(f"\nSummary:\n{state["summary"]}")

# test report generation
# state = report_compiler({"messages": [], "title": "Report Title", "summary": "summary text here", 
#                          "stats_summary": [HumanMessage(content="stats here")], "llm_model": "llm here"})

