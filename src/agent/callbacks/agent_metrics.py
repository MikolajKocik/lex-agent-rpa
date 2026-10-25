import time

from langchain_core.callbacks import BaseCallbackHandler

from src.api.metrics import (
    LAR_AGENT_EXECUTION_SECONDS, 
    LAR_LLM_REQUESTS_TOTAL, 
    LAR_AGENT_TOOL_CALLS_TOTAL,
    LAR_LLM_TOKENS_TOTAL
)


class AgentMetricsCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        super().__init__()
        self._start_times: dict[str, float] = {}
        self._tool_names: dict[str, str] = {}

    def on_chain_start(self, serialized, inputs, *, run_id, parent_run_id=None, **kwargs):
        if parent_run_id is None:
            self._start_times[str(run_id)] = time.perf_counter()

    def on_chain_end(self, outputs, *, run_id, parent_run_id=None, **kwargs):
        if parent_run_id is None and str(run_id) in self._start_times:
            duration = time.perf_counter() - self._start_times.pop(str(run_id))
            LAR_AGENT_EXECUTION_SECONDS.observe(duration)

    def on_chain_error(self, error, *, run_id, parent_run_id=None, **kwargs):
        if parent_run_id is None and str(run_id) in self._start_times:
            duration = time.perf_counter() - self._start_times.pop(str(run_id))
            LAR_AGENT_EXECUTION_SECONDS.observe(duration) 

    def on_tool_start(self, serialized, input_str, *, run_id=None, **kwargs):
        name = (serialized or {}).get("name") or kwargs.get("name") or "tool"
        if run_id:
            self._tool_names[str(run_id)] = name

    def on_tool_end(self, output, *, run_id=None, **kwargs):
        tool_name = self._tool_names.pop(str(run_id), kwargs.get("name", "tool"))
        LAR_AGENT_TOOL_CALLS_TOTAL.labels(
            tool_name=tool_name, 
            status="success"
        ).inc()

    def on_tool_error(self, error, *, run_id=None, **kwargs):
        tool_name = self._tool_names.pop(str(run_id), kwargs.get("name", "tool"))
        LAR_AGENT_TOOL_CALLS_TOTAL.labels(
            tool_name=tool_name,
            status="error"
        ).inc()

    def on_llm_end(self, response, **kwargs):
        LAR_LLM_REQUESTS_TOTAL.labels(
            model="google",
            status="200"
        ).inc()

        input_tokens = 0
        output_tokens = 0

        # LangChain usage_metadata attached to ChatGeneration message
        if response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    msg = getattr(gen, "message", None)
                    usage = getattr(msg, "usage_metadata", None) or {}
                    input_tokens += usage.get("input_tokens", 0)
                    output_tokens += usage.get("output_tokens", 0)

        # llm_output token_usage fallback (Google / OpenAI format)
        if not (input_tokens or output_tokens):
            usage = (response.llm_output or {}).get("token_usage") or {}
            input_tokens = usage.get("prompt_tokens") or usage.get("prompt_token_count", 0)
            output_tokens = usage.get("completion_tokens") or usage.get("candidates_token_count", 0)

        if input_tokens > 0:
            LAR_LLM_TOKENS_TOTAL.labels(model="google", type="input").inc(input_tokens)
        if output_tokens > 0:
            LAR_LLM_TOKENS_TOTAL.labels(model="google", type="output").inc(output_tokens)
    
    def on_llm_error(self, error, **kwargs):
        status = "429" if "429" in str(error) else "error"
        LAR_LLM_REQUESTS_TOTAL.labels(
            model="google",
            status=status
        ).inc()
