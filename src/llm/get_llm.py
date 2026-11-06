from langchain_ollama import ChatOllama
from langchain_openrouter import ChatOpenRouter

USE_OLLAMA = True  # Set to False to use OpenRouter instead

# free models
# OLLAMA_MODEL = "gemma4:31b-cloud"
# OLLAMA_MODEL = "beam:cloud"
# OLLAMA_MODEL = "nemotron-3-nano:30b-cloud"
OLLAMA_MODEL = "gpt-oss:120b-cloud"
# locally served by Ollama
# OLLAMA_MODEL = "gemma4:12b-it-qat"

# OPENROUTER_MODEL = "recursive/flint-v1.0:free"
# OPENROUTER_MODEL = "google/gemma-4-31b-it:free"
OPENROUTER_MODEL = "nvidia/nemotron-3.5-super-vl:free"

# speech models
OLLAMA_SPEECH_MODEL = "phonon:latest"

TEMPERATURE_REPORT_WRITING = 0.8
TEMPERATURE_TOOL_CALLING = 0.0

def get_report_writing_llm():
    # Ollama
    if USE_OLLAMA:
        return ChatOllama(model=OLLAMA_MODEL, temperature=TEMPERATURE_REPORT_WRITING)
    else:
        # OpenRouter
        return ChatOpenRouter(
            model=OPENROUTER_MODEL,
            temperature=TEMPERATURE_REPORT_WRITING,
        # max_tokens=1024,
        # max_retries=2
        )

def get_toolcalling_llm():
    # Ollama
    if USE_OLLAMA:
        return ChatOllama(model=OLLAMA_MODEL, temperature=TEMPERATURE_TOOL_CALLING)
    else:
        # OpenRouter
        return ChatOpenRouter(
            model=OPENROUTER_MODEL,
            temperature=TEMPERATURE_TOOL_CALLING,
        # max_tokens=1024,
        # max_retries=2
        )

# Other models I tested but didn't perform as well for this use case:
# works well but sometimes wrong analysis
# llm = ChatOllama(model="qwen3-coder:480b-cloud", temperature=0)

#didn't know how to use tools
# llm = ChatOllama(model="gemma3:4b-cloud", temperature=0)  

#local models for testing
# llm = ChatOllama(model="PetrosStav/gemma3-tools:4b", temperature=0) # confused with player names

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI

def get_report_writing_llm_gemini():
    return ChatGoogleGenerativeAI(
        # model="gemini-3.5-flash",
        model="gemini-3.1-flash-lite",
        # model="gemini-2.5-flash",   #hit rate limit
        # model="gemini-2.5-flash-lite", #didn't use tool calls effectively
        temperature=0.9,  # Gemini 3.0+ defaults to 1.0
        max_tokens=None,
        timeout=None,
        max_retries=2,
        # other params...
    )

def get_toolcalling_llm_gemini():
    return ChatGoogleGenerativeAI(
        # model="gemini-3.5-flash",
        model="gemini-3.1-flash-lite",
        # model="gemini-2.5-flash", # hit rate limit
        # model="gemini-2.5-flash-lite", # didn't use tool calls effectively
        temperature=0.0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        # other params...
    )