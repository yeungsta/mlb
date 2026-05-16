from langchain_ollama import ChatOllama

def get_report_writing_llm():
    # Z AI's GLM-5: A strong reasoning and agentic model from Z.ai with 744B total parameters (40B active), built for complex systems engineering and long-horizon tasks
    # Made awesome analysis! Fast too. Got tool usage order correct consistently in testing.
    # needs subscription
    # return ChatOllama(model="glm-5:cloud", temperature=0)
    # Moonshot AI's native multimodal agentic model that seamlessly integrates vision and language understanding with advanced agentic capabilities, 
    # instant and thinking modes, as well as conversational and agentic paradigms
    # Made awesome analysis! Cheaper token usage. Did not get tool usage order correct consistently in testing (sometimes called head-to-head stats tool before looking up player ids, which caused an error since the tool didn't have the necessary information to make the call)
    # needs subscription
    # return ChatOllama(model="kimi-k2.6:cloud", temperature=0)

    # didn't use Vin Scully style language
    # return ChatOllama(model="qwen3-coder:480b-cloud", temperature=0.8)
    # didn't use Vin Scully style language
    # return ChatOllama(model="qwen3-coder-next:cloud", temperature=0.8)
    # didn't use Vin Scully style language
    # return ChatOllama(model="nemotron-3-super:cloud", temperature=0.8)
    # good summary, but cannot do structured output, which makes it difficult to extract the summary + title for use in the final report
    return ChatOllama(model="gemma4:31b-cloud", temperature=0.8)

def get_toolcalling_llm():
    return ChatOllama(model="gemma4:31b-cloud", temperature=0)

    # temp 0.0: basic summary
    # return ChatOllama(model="qwen3-coder-next:cloud", temperature=0)

    # return ChatOllama(model="minimax-m2.7:cloud", temperature=0)    # needs subscription
    # return ChatOllama(model="qwen3.5:397b-cloud", temperature=0)    # needs subscription

# Other models I tested but didn't perform as well for this use case:
# works well but sometimes wrong analysis
# llm = ChatOllama(model="qwen3-coder:480b-cloud", temperature=0)

#didn't know how to use tools
# llm = ChatOllama(model="gemma3:4b-cloud", temperature=0)  

#local models for testing
# llm = ChatOllama(model="PetrosStav/gemma3-tools:4b", temperature=0) # confused with player names