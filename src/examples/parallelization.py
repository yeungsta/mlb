from typing import TypedDict

from typing_extensions import Literal

from langchain.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain.messages import SystemMessage, HumanMessage, ToolMessage

from langchain_ollama import ChatOllama

# Initialize the model
# llm = ChatOllama(model="qwen3-coder:480b-cloud", temperature=0)
llm = ChatOllama(model="gemma3:4b-cloud", temperature=0)
#local models for testing
# llm = ChatOllama(model="PetrosStav/gemma3-tools:4b", temperature=0)

# Graph state
class State(TypedDict):
    topic: str
    joke: str
    story: str
    poem: str
    combined_output: str


# Nodes
def call_llm_1(state: State):
    """First LLM call to generate initial joke"""

    msg = llm.invoke(f"Write a short joke about {state['topic']}; do not include any other text, just the joke itself.")
    return {"joke": msg.content}


def call_llm_2(state: State):
    """Second LLM call to generate story"""

    msg = llm.invoke(f"Write a short story about {state['topic']}; do not include any other text, just the story itself. Limit to 4 sentences.")
    return {"story": msg.content}


def call_llm_3(state: State):
    """Third LLM call to generate poem"""

    msg = llm.invoke(f"Write a short poem about {state['topic']}; do not include any other text, just the poem itself. Limit to 4 lines.")
    return {"poem": msg.content}


def aggregator(state: State):
    """Combine the joke, story and poem into a single output"""

    combined = f"Here's a story, joke, and poem about {state['topic']}!\n\n"
    combined += f"STORY:\n{state['story']}\n\n"
    combined += f"JOKE:\n{state['joke']}\n\n"
    combined += f"POEM:\n{state['poem']}"
    return {"combined_output": combined}


# Build workflow
parallel_builder = StateGraph(State)

# Add nodes
parallel_builder.add_node("call_llm_1", call_llm_1)
parallel_builder.add_node("call_llm_2", call_llm_2)
parallel_builder.add_node("call_llm_3", call_llm_3)
parallel_builder.add_node("aggregator", aggregator)

# Add edges to connect nodes
parallel_builder.add_edge(START, "call_llm_1")
parallel_builder.add_edge(START, "call_llm_2")
parallel_builder.add_edge(START, "call_llm_3")
parallel_builder.add_edge("call_llm_1", "aggregator")
parallel_builder.add_edge("call_llm_2", "aggregator")
parallel_builder.add_edge("call_llm_3", "aggregator")
parallel_builder.add_edge("aggregator", END)
parallel_workflow = parallel_builder.compile()

# Invoke
# state = parallel_workflow.invoke({"topic": "software developers"})
# print(state["combined_output"])