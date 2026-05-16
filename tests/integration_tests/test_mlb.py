import pytest
from langchain.agents import create_agent
from langchain.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage

from src.mlb_single_agent_retriever import build_graph
from models import state

def assert_tool_calls(messages, expected_tool_calls):
    tool_calls = [
        tc
        for msg in messages
        if hasattr(msg, "tool_calls")
        for tc in (msg.tool_calls or [])
    ]
    tool_call_names = [tc["name"] for tc in tool_calls]
    for expected in expected_tool_calls:
        assert expected in tool_call_names, f"Expected tool call '{expected}' not found in {tool_call_names}"

def assert_final_message(messages):
    assert isinstance(messages[-1], AIMessage), f"Expected last message to be AIMessage, got {type(messages[-1])}"
    assert len(messages[-1].content) > 0, "Expected last message content to be non-empty"
    assert len(messages) > 1, "Expected more than one message in the conversation"

# @pytest.mark.vcr()
def test_starting_pitcher_vs_opposing_lineup():
    graph = build_graph()

    # messages = [HumanMessage(content="Analyze today's Dodger's starting pitcher vs. the opposing lineup.")]
    messages = [HumanMessage(content="Analyze today's Angels game's starting pitcher vs. the opposing lineup.")]
    # messages = [HumanMessage(content="Analyze today's Mariners game's starting pitcher vs. the opposing lineup.")]
    # messages = [HumanMessage(content="Analyze today's Tigers game's starting pitcher vs. the opposing lineup.")]

    result = graph.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]

    for m in result["messages"]:
        m.pretty_print()
        
    #print final summary analysis for debugging
    title = result["title"]
    summary = result["summary"]
    print(f"\n{title}")
    print(f"\n{summary}")

    assert_final_message(result["messages"])

    expected_tool_calls = ["current_date", "retrieve_current_player_id", 
         "retrieve_pitcher_pitch_type_stats_past_year", "retrieve_season_pitching_stats", 
         "retrieve_batter_exit_velo_stats_past_year", "retrieve_season_hitting_stats", 
         "head_to_head_stats", "retrieve_game_id", "game_info", "starting_lineups"]
    assert_tool_calls(result["messages"], expected_tool_calls=expected_tool_calls)

def test_individual_pitcher_analysis():
    graph = build_graph()

    # messages = [HumanMessage(content="Analyze Alex Vesia's stats")]
    # messages = [HumanMessage(content="Analyze Justin Wrobleski's stats")]
    # messages = [HumanMessage(content="Analyze Roki Sasaki's stats")]
    messages = [HumanMessage(content="Analyze Yoshinobu Yamamoto's stats")]

    result = graph.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]

    for m in result["messages"]:
        m.pretty_print()
        

    assert_final_message(result["messages"])

    expected_tool_calls = ["current_date", "retrieve_current_player_id", 
         "retrieve_pitcher_pitch_type_stats_past_year", "retrieve_season_pitching_stats"]
    assert_tool_calls(result["messages"], expected_tool_calls=expected_tool_calls)

def test_individual_batter_analysis():
    graph = build_graph()

    # messages = [HumanMessage(content="Analyze Kazuma Okamoto's stats")]
    # messages = [HumanMessage(content="Analyze Andy Page's stats")]
    # messages = [HumanMessage(content="Analyze Mookie Betts's stats")]
    messages = [HumanMessage(content="Analyze Teoscar Hernandez's stats")]

    result = graph.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]

    for m in result["messages"]:
        m.pretty_print()
        
    assert_final_message(result["messages"])

    expected_tool_calls = ["current_date", "retrieve_current_player_id", 
                           "retrieve_batter_exit_velo_stats_past_year", "retrieve_season_hitting_stats"]
    assert_tool_calls(result["messages"], expected_tool_calls=expected_tool_calls)

def test_head_to_head_analysis():
    graph = build_graph()

    # messages = [HumanMessage(content="Head to head stats for Dylan Cease vs. Mookie Betts.")]
    messages = [HumanMessage(content="Mike Trout vs. Clayton Kershaw")]
    # messages = [HumanMessage(content="Dylan Cease vs. Mookie Betts")]
    # messages = [HumanMessage(content="Clayton Kershaw vs. Mike Trout")]

    result = graph.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]

    for m in result["messages"]:
        m.pretty_print()
        
    assert_final_message(result["messages"])

    expected_tool_calls = ["current_date", "retrieve_current_player_id", 
                           "retrieve_pitcher_pitch_type_stats_past_year", "retrieve_season_pitching_stats", 
                            "retrieve_batter_exit_velo_stats_past_year", "retrieve_season_hitting_stats", 
                            "head_to_head_stats"]
    assert_tool_calls(result["messages"], expected_tool_calls=expected_tool_calls)

def test_game_info():
    graph = build_graph()

    messages = [HumanMessage(content="When's the next game for the Dodgers, who are the starting pitchers, and what are the lineups of both teams?")]
    # messages = [HumanMessage(content="Info on today's Dodgers game")]
    # messages = [HumanMessage(content="Analyze today's Dodgers game's starting pitchers.")]

    result = graph.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]

    for m in result["messages"]:
        m.pretty_print()
        
    assert_final_message(result["messages"])

    expected_tool_calls = ["current_date", "retrieve_game_id", "game_info", "starting_lineups"]
    assert_tool_calls(result["messages"], expected_tool_calls=expected_tool_calls)


