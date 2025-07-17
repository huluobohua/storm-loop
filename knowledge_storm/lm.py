import logging
import os
import random
import threading
from typing import Optional, Literal, Any


try:
    import dspy
except ModuleNotFoundError:  # pragma: no cover - handled for optional dep
    dspy = None

# Install compatibility shim for legacy dspy imports
from dspy_compatibility_shim import install_dspy_compatibility_shim
install_dspy_compatibility_shim()

import requests

# Legacy import removed - TGIClient now uses modern dspy.HFClientTGI
# from dspy.dsp.modules.hf_client import send_hftgi_request_v01_wrapped
from openai import OpenAI
from transformers import AutoTokenizer

try:
    from anthropic import RateLimitError
except ImportError:
    RateLimitError = None


class OpenAIModel(dspy.LM):
    """A wrapper class for dspy.OpenAI with enhanced token usage tracking."""

    def __init__(
        self,
        model: str = "gpt-3.5-turbo-instruct",
        api_key: Optional[str] = None,
        model_type: Literal["chat", "text"] = None,
        **kwargs,
    ):
        # Initialize parent with model parameter
        super().__init__(model=model)
        
        # Create internal dspy.OpenAI instance for delegation
        self._openai_client = dspy.OpenAI(
            model=model,
            api_key=api_key,
            model_type=model_type,
            **kwargs
        )
        
        # Token usage tracking
        self._token_usage_lock = threading.Lock()
        self.prompt_tokens = 0
        self.completion_tokens = 0
        
        # Store parameters for backward compatibility
        self.api_key = api_key
        self.model_type = model_type

    def log_usage(self, response):
        """Log the total tokens from the OpenAI API response."""
        usage_data = response.get("usage")
        if usage_data:
            with self._token_usage_lock:
                self.prompt_tokens += usage_data.get("prompt_tokens", 0)
                self.completion_tokens += usage_data.get("completion_tokens", 0)

    def get_usage_and_reset(self):
        """Get the total tokens used and reset the token usage."""
        model_name = self._openai_client.kwargs.get("model") or self.kwargs.get("model")
        usage = {
            model_name: {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
            }
        }
        self.prompt_tokens = 0
        self.completion_tokens = 0

        return usage

    def basic_request(self, prompt: str, **kwargs):
        """Core request method that delegates to the internal OpenAI client"""
        response = self._openai_client.basic_request(prompt, **kwargs)
        
        # Log token usage from the response
        self.log_usage(response)
        
        return response

    def _get_choice_text(self, choice: dict[str, Any]) -> str:
        """Extract text from a choice response based on model type"""
        if self._openai_client.model_type == "chat":
            return choice["message"]["content"]
        return choice["text"]

    def __call__(
        self,
        prompt: str,
        only_completed: bool = True,
        return_sorted: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Copied from dspy/dsp/modules/gpt3.py with the addition of tracking token usage."""

        assert only_completed, "for now"
        assert return_sorted is False, "for now"

        # if kwargs.get("n", 1) > 1:
        #     if self.model_type == "chat":
        #         kwargs = {**kwargs}
        #     else:
        #         kwargs = {**kwargs, "logprobs": 5}

        response = self.basic_request(prompt, **kwargs)

        # Token usage is already logged in basic_request

        choices = response["choices"]

        completed_choices = [c for c in choices if c["finish_reason"] != "length"]

        if only_completed and len(completed_choices):
            choices = completed_choices

        completions = [self._get_choice_text(c) for c in choices]
        if return_sorted and kwargs.get("n", 1) > 1:
            scored_completions = []

            for c in choices:
                tokens, logprobs = (
                    c["logprobs"]["tokens"],
                    c["logprobs"]["token_logprobs"],
                )

                if "<|endoftext|>" in tokens:
                    index = tokens.index("<|endoftext|>") + 1
                    tokens, logprobs = tokens[:index], logprobs[:index]

                avglog = sum(logprobs) / len(logprobs)
                scored_completions.append((avglog, self._get_choice_text(c)))

            scored_completions = sorted(scored_completions, reverse=True)
            completions = [c for _, c in scored_completions]

        return completions


class DeepSeekModel(dspy.LM):
    """A wrapper class for DeepSeek API using modern dspy patterns."""

    def __init__(
        self,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        api_base: str = "https://api.deepseek.com",
        **kwargs,
    ):
        # Initialize parent with model parameter only
        super().__init__(model=model)
        
        # Store DeepSeek-specific parameters
        self.model = model
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.api_base = api_base
        
        if not self.api_key:
            raise ValueError(
                "DeepSeek API key must be provided either as an argument or as an environment variable DEEPSEEK_API_KEY"
            )
        
        # Token usage tracking
        self._token_usage_lock = threading.Lock()
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def log_usage(self, response):
        """Log the total tokens from the DeepSeek API response."""
        usage_data = response.get("usage")
        if usage_data:
            with self._token_usage_lock:
                self.prompt_tokens += usage_data.get("prompt_tokens", 0)
                self.completion_tokens += usage_data.get("completion_tokens", 0)

    def get_usage_and_reset(self):
        """Get the total tokens used and reset the token usage."""
        usage = {
            self.model: {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
            }
        }
        self.prompt_tokens = 0
        self.completion_tokens = 0
        return usage

    def basic_request(self, prompt: str, **kwargs):
        """Core request method implementing the abstract method from dspy.LM"""
        response = self._create_completion(prompt, **kwargs)
        
        # Log token usage from the response
        self.log_usage(response)
        
        return response
    
    def _create_completion(self, prompt: str, **kwargs):
        """Create a completion using the DeepSeek API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs,
        }
        response = requests.post(
            f"{self.api_base}/v1/chat/completions", headers=headers, json=data
        )
        response.raise_for_status()
        return response.json()

    def __call__(
        self,
        prompt: str,
        only_completed: bool = True,
        return_sorted: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Call the DeepSeek API to generate completions."""
        assert only_completed, "for now"
        assert return_sorted is False, "for now"

        response = self.basic_request(prompt, **kwargs)

        # Token usage is already logged in basic_request

        choices = response["choices"]
        completions = [choice["message"]["content"] for choice in choices]

        history = {
            "prompt": prompt,
            "response": response,
            "kwargs": kwargs,
        }
        self.history.append(history)

        return completions


class OllamaClient(dspy.LM):
    """A wrapper class for dspy.OllamaClient."""

    def __init__(self, model, port, url="http://localhost", **kwargs):
        """Copied from dspy/dsp/modules/hf_client.py with the addition of storing additional kwargs."""
        # Check if the URL has 'http://' or 'https://'
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        super().__init__(model=model, base_url=f"{url}:{port}", **kwargs)
        # Store additional kwargs for the generate method.
        self.kwargs = {**self.kwargs, **kwargs}


class TGIClient(dspy.LM):
    """Modern TGI client using dspy.HFClientTGI instead of legacy mock functions"""
    
    def __init__(self, model, port, url, http_request_kwargs=None, **kwargs):
        # Initialize with modern dspy.HFClientTGI
        self._modern_client = dspy.HFClientTGI(
            model=model,
            port=port,
            url=url,
            http_request_kwargs=http_request_kwargs or {},
            **kwargs
        )
        
        # Also initialize parent for compatibility
        super().__init__(
            model=model,
            **kwargs
        )
        
        # Store original parameters for backward compatibility
        self.model = model
        self.port = port
        self.url = url
        self.ports = [port] if isinstance(port, int) else port  # Support single port or list
        self.headers = {}
        self.http_request_kwargs = http_request_kwargs or {}

    def basic_request(self, prompt: str, **kwargs):
        """Delegate to modern dspy.HFClientTGI basic_request method"""
        return self._modern_client.basic_request(prompt, **kwargs)
    
    def __call__(self, prompt: str, only_completed: bool = True, return_sorted: bool = False, **kwargs):
        """Delegate to modern dspy.HFClientTGI __call__ method"""
        return self._modern_client(prompt, only_completed=only_completed, return_sorted=return_sorted, **kwargs)
    
    def _generate(self, prompt, **kwargs):
        """Legacy method for backward compatibility - delegates to modern implementation"""
        return self.basic_request(prompt, **kwargs)
    
    def generate(self, prompt, **kwargs):
        """Public generate method for compatibility"""
        return self.__call__(prompt, **kwargs)


class TogetherClient(dspy.LM):
    """A wrapper class for dspy.Together."""

    def __init__(
        self,
        model,
        apply_tokenizer_chat_template=False,
        hf_tokenizer_name=None,
        **kwargs,
    ):
        """Copied from dspy/dsp/modules/hf_client.py with the support of applying tokenizer chat template."""

        super().__init__(model=model, is_client=True)
        self.session = requests.Session()
        self.api_base = (
            "https://api.together.xyz/v1/completions"
            if os.getenv("TOGETHER_API_BASE") is None
            else os.getenv("TOGETHER_API_BASE")
        )
        self.token = os.getenv("TOGETHER_API_KEY")
        self.model = model

        # self.use_inst_template = False
        # if any(keyword in self.model.lower() for keyword in ["inst", "instruct"]):
        #     self.use_inst_template = True
        self.apply_tokenizer_chat_template = apply_tokenizer_chat_template
        if self.apply_tokenizer_chat_template:
            logging.info("Loading huggingface tokenizer.")
            if hf_tokenizer_name is None:
                hf_tokenizer_name = self.model
            self.tokenizer = AutoTokenizer.from_pretrained(
                hf_tokenizer_name, cache_dir=kwargs.get("cache_dir", None)
            )

        stop_default = "\n\n---"

        self.kwargs = {
            "temperature": kwargs.get("temperature", 0.0),
            "max_tokens": 512,
            "top_p": 1,
            "top_k": 1,
            "repetition_penalty": 1,
            "n": 1,
            "stop": stop_default if "stop" not in kwargs else kwargs["stop"],
            **kwargs,
        }
        self._token_usage_lock = threading.Lock()
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def log_usage(self, response):
        """Log the total tokens from the OpenAI API response."""
        usage_data = response.get("usage")
        if usage_data:
            with self._token_usage_lock:
                self.prompt_tokens += usage_data.get("prompt_tokens", 0)
                self.completion_tokens += usage_data.get("completion_tokens", 0)

    def get_usage_and_reset(self):
        """Get the total tokens used and reset the token usage."""
        usage = {
            self.model: {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
            }
        }
        self.prompt_tokens = 0
        self.completion_tokens = 0

        return usage

    def basic_request(self, prompt: str, **kwargs):
        raw_kwargs = kwargs
        kwargs = {
            **self.kwargs,
            **kwargs,
        }

        # Google disallows "n" arguments.
        n = kwargs.pop("n", None)

        response = self.llm.generate_content(prompt, generation_config=kwargs)

        history = {
            "prompt": prompt,
            "response": [response.to_dict()],
            "kwargs": kwargs,
            "raw_kwargs": raw_kwargs,
        }
        self.history.append(history)

        return response

    
    def request(self, prompt: str, **kwargs):
        """Handles retrieval of completions from Google whilst handling API errors."""
        return self.basic_request(prompt, **kwargs)

    def __call__(
        self,
        prompt: str,
        only_completed: bool = True,
        return_sorted: bool = False,
        **kwargs,
    ):
        assert only_completed, "for now"
        assert return_sorted is False, "for now"

        n = kwargs.pop("n", 1)

        completions = []
        for _ in range(n):
            response = self.request(prompt, **kwargs)
            self.log_usage(response)
            completions.append(response.parts[0].text)

        return completions
