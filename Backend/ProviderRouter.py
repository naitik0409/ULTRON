import time
import random
import logging
from typing import Optional, Callable
from dotenv import dotenv_values
from openai import OpenAI
import itertools

logger = logging.getLogger("ProviderRouter")

env = dotenv_values(".env")


def _client(api_key: str, base_url: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url=base_url)


class ProviderEndpoint:
    def __init__(self, name: str, api_key: str, base_url: str, model: str, weight: int = 1):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.weight = weight
        self._client = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = _client(self.api_key, self.base_url)
        return self._client


class ProviderChain:
    def __init__(self, name: str, endpoints: list[ProviderEndpoint], retry_count: int = 2, backoff_base: float = 2.0):
        self.name = name
        self.endpoints = endpoints
        self.retry_count = retry_count
        self.backoff_base = backoff_base
        self._cycle = itertools.cycle(endpoints) if endpoints else iter([])

    def query(self, messages: list, temperature: float = 0.7, max_tokens: int = 1024, stream: bool = False, **kwargs) -> str:
        if not self.endpoints:
            raise ValueError(f"No endpoints configured for chain '{self.name}'")

        last_error = None

        for attempt in range(self.retry_count + 1):
            endpoint = next(self._cycle)
            try:
                if stream:
                    response = endpoint.client.chat.completions.create(
                        model=endpoint.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True,
                        **kwargs
                    )
                    full = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full += chunk.choices[0].delta.content
                    return full
                else:
                    response = endpoint.client.chat.completions.create(
                        model=endpoint.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                    return response.choices[0].message.content

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                logger.warning(f"Provider '{endpoint.name}' failed on {endpoint.model}: {e}")

                if "rate" in error_str or "quota" in error_str or "limit" in error_str or "429" in error_str:
                    time.sleep(self.backoff_base ** attempt + random.uniform(0, 1))
                    continue

                if attempt < self.retry_count:
                    time.sleep(0.5 * (attempt + 1))
                    continue

                raise

        raise last_error or RuntimeError(f"All providers failed for chain '{self.name}'")


class ProviderRouter:
    def __init__(self):
        self.chains: dict[str, ProviderChain] = {}
        self._build_chains()

    def _build_chains(self):
        groq_key = env.get("GroqAPIKey")
        coding_groq_key = env.get("CodingGroqAPIKey") or groq_key
        openrouter_keys = [env.get(f"OpenRouterAPIKey{i}") for i in range(1, 7)]
        openrouter_keys = [k for k in openrouter_keys if k]
        deepseek_key = env.get("DeepSeekAPIKey")

        groq_endpoints = []
        if groq_key:
            groq_endpoints.append(ProviderEndpoint("groq", groq_key, "https://api.groq.com/openai/v1", env.get("GroqChatModel", "llama-3.3-70b-versatile"), weight=5))
        if coding_groq_key and coding_groq_key != groq_key:
            groq_endpoints.append(ProviderEndpoint("groq_coding", coding_groq_key, "https://api.groq.com/openai/v1", env.get("GroqChatModel", "llama-3.3-70b-versatile"), weight=3))

        openrouter_endpoints = []
        for i, key in enumerate(openrouter_keys):
            openrouter_endpoints.append(ProviderEndpoint(f"openrouter_{i+1}", key, "https://openrouter.ai/api/v1", "deepseek/deepseek-chat", weight=2))

        deepseek_endpoints = []
        if deepseek_key:
            deepseek_endpoints.append(ProviderEndpoint("deepseek", deepseek_key, "https://api.deepseek.com", "deepseek-chat", weight=4))

        self.chains["general"] = ProviderChain("general", groq_endpoints)
        self.chains["realtime_search"] = ProviderChain("realtime_search", groq_endpoints)
        self.chains["coding_orchestrator"] = ProviderChain("coding_orchestrator", openrouter_endpoints or deepseek_endpoints or groq_endpoints)
        self.chains["coding_reasoning"] = ProviderChain("coding_reasoning", openrouter_endpoints or deepseek_endpoints or groq_endpoints)
        self.chains["coding_codegen"] = ProviderChain("coding_codegen", openrouter_endpoints or deepseek_endpoints or groq_endpoints)
        self.chains["coding_editing"] = ProviderChain("coding_editing", openrouter_endpoints or deepseek_endpoints or groq_endpoints)
        self.chains["coding_debugger"] = ProviderChain("coding_debugger", groq_endpoints)
        self.chains["coding_explainer"] = ProviderChain("coding_explainer", groq_endpoints or openrouter_endpoints)
        self.chains["coding_genai"] = ProviderChain("coding_genai", openrouter_endpoints or deepseek_endpoints or groq_endpoints)

    def get_chain(self, name: str) -> ProviderChain:
        chain = self.chains.get(name)
        if not chain:
            raise ValueError(f"Unknown provider chain: {name}. Available: {list(self.chains.keys())}")
        return chain

    def query(self, chain_name: str, messages: list, temperature: float = 0.7, max_tokens: int = 1024, stream: bool = False, **kwargs) -> str:
        chain = self.get_chain(chain_name)
        return chain.query(messages, temperature=temperature, max_tokens=max_tokens, stream=stream, **kwargs)

    def stream_to_console(self, chain_name: str, messages: list, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        chain = self.get_chain(chain_name)
        return chain.query(messages, temperature=temperature, max_tokens=max_tokens, stream=True, **kwargs)

    def get_available_chains(self) -> list[str]:
        return list(self.chains.keys())


router = ProviderRouter()


def get_router() -> ProviderRouter:
    return router
