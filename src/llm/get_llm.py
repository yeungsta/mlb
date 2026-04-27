from langchain_ollama import ChatOllama

def get_heavyweight_llm():
    # Z AI's GLM-5: A strong reasoning and agentic model from Z.ai with 744B total parameters (40B active), built for complex systems engineering and long-horizon tasks
    # Made awesome analysis! Fast too. Got tool usage order correct consistently in testing.
    # needs subscription
    # return ChatOllama(model="glm-5:cloud", temperature=0)
    # Moonshot AI's native multimodal agentic model that seamlessly integrates vision and language understanding with advanced agentic capabilities, 
    # instant and thinking modes, as well as conversational and agentic paradigms
    # Made awesome analysis! Cheaper token usage. Did not get tool usage order correct consistently in testing (sometimes called head-to-head stats tool before looking up player ids, which caused an error since the tool didn't have the necessary information to make the call)
    # needs subscription
    return ChatOllama(model="kimi-k2.6:cloud", temperature=0)

def get_lightweight_llm():
    # return ChatOllama(model="qwen3-coder:480b-cloud", temperature=0)
    return ChatOllama(model="minimax-m2.7:cloud", temperature=0)


# Other models I tested but didn't perform as well for this use case:
# works well but sometimes wrong analysis
# llm = ChatOllama(model="qwen3-coder:480b-cloud", temperature=0)

#didn't know how to use tools
# llm = ChatOllama(model="gemma3:4b-cloud", temperature=0)  

#local models for testing
# llm = ChatOllama(model="PetrosStav/gemma3-tools:4b", temperature=0) # confused with player names