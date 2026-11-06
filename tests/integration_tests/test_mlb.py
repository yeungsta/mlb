import os
from urllib import response

import pytest
from langchain.agents import create_agent
from langchain.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage

from src.mlb_single_agent_retriever import build_graph
from models import state

SPEECH_PLAYBACK_ENABLED = True  # Set to False to disable speech playback during tests
# Set to the desired voice for speech playback
# american accent:
# SPEECH_VOICE = "Zoey"  
# SPEECH_VOICE = "Easton"
# british accent:
# SPEECH_VOICE = "Freya"
# SPEECH_VOICE = "Spencer"
# interesting characters
# SPEECH_VOICE = "Old Mortlake"
SPEECH_VOICE = "The Thing Under the Stairs"

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
    # messages = [HumanMessage(content="Analyze today's Brewers' starting pitcher vs. the opposing lineup.")]
    messages = [HumanMessage(content="Analyze today's Rays' starting pitcher vs. the opposing lineup.")]
    # messages = [HumanMessage(content="Analyze today's White Sox's starting pitcher vs. the opposing lineup.")]
    # messages = [HumanMessage(content="Analyze today's Phillies game's starting pitcher vs. the opposing lineup.")]
    # messages = [HumanMessage(content="Analyze today's Mariners game's starting pitcher vs. the opposing lineup.")]
    # messages = [HumanMessage(content="Analyze today's Tigers game's starting pitcher vs. the opposing lineup.")]

    result = graph.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]

    for m in result["messages"]:
        m.pretty_print()
        
    if SPEECH_PLAYBACK_ENABLED:
        speak_results(result)

    assert_final_message(result["messages"])

    expected_tool_calls = ["current_date", 
                        #    "retrieve_current_player_id", # sometimes the historical player id retrieval tool is called before the current player id retrieval tool
         "retrieve_pitcher_pitch_type_stats_past_year", "retrieve_season_pitching_stats", 
         "retrieve_batter_exit_velo_stats_past_year", "retrieve_season_hitting_stats", 
         "head_to_head_stats", "retrieve_game_id", "game_info", "starting_lineups"]
    assert_tool_calls(result["messages"], expected_tool_calls=expected_tool_calls)

def test_individual_pitcher_analysis():
    graph = build_graph()

    # messages = [HumanMessage(content="Analyze Alex Vesia's stats")]
    # messages = [HumanMessage(content="Analyze Justin Wrobleski's stats")]
    # messages = [HumanMessage(content="Analyze Roki Sasaki's stats")]
    # messages = [HumanMessage(content="Analyze Yoshinobu Yamamoto's stats")]
    # messages = [HumanMessage(content="Analyze Emmet Sheehan's stats")]
    # messages = [HumanMessage(content="Analyze Edwin Diaz's stats")]
    # messages = [HumanMessage(content="Analyze Blake Snell's stats this season")]
    messages = [HumanMessage(content="Analyze Trevor Megill's stats this season")]

    result = graph.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]

    for m in result["messages"]:
        m.pretty_print()
        
    if SPEECH_PLAYBACK_ENABLED:
        speak_results(result)

    assert_final_message(result["messages"])

    expected_tool_calls = ["current_date", 
                        #    "retrieve_current_player_id", # sometimes the historical player id retrieval tool is called before the current player id retrieval tool
         "retrieve_pitcher_pitch_type_stats_past_year", "retrieve_season_pitching_stats"]
    assert_tool_calls(result["messages"], expected_tool_calls=expected_tool_calls)

def test_individual_batter_analysis():
    graph = build_graph()

    # messages = [HumanMessage(content="Analyze Kazuma Okamoto's stats")]
    # messages = [HumanMessage(content="Analyze Andy Page's stats")]
    # messages = [HumanMessage(content="Analyze Mookie Betts's stats")]
    # messages = [HumanMessage(content="Analyze Teoscar Hernandez's stats")]
    messages = [HumanMessage(content="Analyze Tommy Edman's stats")]

    result = graph.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]

    for m in result["messages"]:
        m.pretty_print()

    if SPEECH_PLAYBACK_ENABLED:
        speak_results(result)

    assert_final_message(result["messages"])

    expected_tool_calls = ["current_date", 
                        #    "retrieve_current_player_id", # sometimes the historical player id retrieval tool is called before the current player id retrieval tool
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

    if SPEECH_PLAYBACK_ENABLED:
        speak_results(result)
        
    assert_final_message(result["messages"])

    expected_tool_calls = ["current_date", "retrieve_current_player_id", 
                           "retrieve_pitcher_pitch_type_stats_past_year", "retrieve_season_pitching_stats", 
                            "retrieve_batter_exit_velo_stats_past_year", "retrieve_season_hitting_stats", 
                            "head_to_head_stats"]
    assert_tool_calls(result["messages"], expected_tool_calls=expected_tool_calls)

def test_game_info():
    graph = build_graph()

    # messages = [HumanMessage(content="When's the next game for the Dodgers, who are the starting pitchers, and what are the lineups of both teams?")]
    # messages = [HumanMessage(content="Info on today's Dodgers game")]
    # messages = [HumanMessage(content="Analyze today's Dodgers game's starting pitchers.")]
    # messages = [HumanMessage(content="When's the next game for the Brewers, who are the starting pitchers, and what are the lineups of both teams?")]
    messages = [HumanMessage(content="When was the previous game for the Brewers, who were the starting pitchers, and what were the lineups of both teams?")]

    result = graph.invoke({"messages": messages}) # pyright: ignore[reportArgumentType]

    for m in result["messages"]:
        m.pretty_print()

    if SPEECH_PLAYBACK_ENABLED:
        speak_results(result)

    assert_final_message(result["messages"])

    expected_tool_calls = ["current_date", "retrieve_game_id", "game_info", "starting_lineups"]
    assert_tool_calls(result["messages"], expected_tool_calls=expected_tool_calls)

def speak_results(result:dict):
    title = result["title"]
    summary = result["summary"]
    speak_text(f"{title}, by Vin Scully AI. {summary}", voice=SPEECH_VOICE)

def speak_text(summary_text:str, voice:str="default"):
    # use speech LLM to speak the title
    from openai import OpenAI

    client = OpenAI(base_url=os.getenv("OLLAMA_API_V1_BASE"), api_key=os.getenv("OLLAMA_API_KEY"))

    print(f"\nSpeaking summary with voice '{voice}': {summary_text}\n")

    with client.audio.speech.with_streaming_response.create(
        model="phonon",
        voice=voice,
        input=summary_text,
        response_format="wav",
    ) as response:
        response.stream_to_file("report_speech.wav")

    #immediately playback the .wav file
    import simpleaudio as sa
    wave_obj = sa.WaveObject.from_wave_file("report_speech.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()
