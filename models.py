import os
from typing import Any

from huggingface_hub import InferenceClient
from langchain_community.embeddings import HuggingFaceEmbeddings

from dotenv import load_dotenv
load_dotenv()


def get_hf_token() -> str:
    token = os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    if not token:
        raise RuntimeError(
            "HUGGINGFACEHUB_API_TOKEN is not set. "
            "Please create a Hugging Face access token and export it as an env var."
        )
    return token


class HFChatModel:
    """
    Minimal wrapper around Hugging Face's chat_completion API.

    It exposes a simple .invoke(prompt: str) -> str interface,
    so you can plug it directly into your existing rephrase/answer nodes.
    """

    def __init__(
        self,
        model_name: str,
        api_token: str,
        temperature: float = 0.2,
        max_new_tokens: int = 256,
    ) -> None:
        self.client = InferenceClient(model=model_name, token=api_token)
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens

    def invoke(self, prompt: str) -> str:
        # Use the chat-completion style API, which is what these models actually support.
        response = self.client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_new_tokens,
            temperature=self.temperature,
        )
        # Grab the generated text from the first choice
        return response.choices[0].message["content"]


def build_llm(
    model_name: str = "google/gemma-2-2b-it",  # you can swap this later
    temperature: float = 0.2,
    max_new_tokens: int = 256,
) -> HFChatModel:
    api_token = get_hf_token()
    return HFChatModel(
        model_name=model_name,
        api_token=api_token,
        temperature=temperature,
        max_new_tokens=max_new_tokens,
    )


def build_embedding_model(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> HuggingFaceEmbeddings:
    """
    Local embedding model using sentence-transformers.

    This runs on your machine, is lightweight, and avoids HF Inference quirks.
    """
    return HuggingFaceEmbeddings(model_name=model_name)
