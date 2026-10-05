from core.config.llm_provider import NvidiaLLMProvider

nvidia_provider = NvidiaLLMProvider(temperature=0.1)
llm = nvidia_provider.get_model()

# TODO