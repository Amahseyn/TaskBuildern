from typing import List, Any
from extractor.llm import LLMClient

class BaseStrategy:
    """Base class for extraction strategies."""
    def __init__(self, client: LLMClient):
        self.client = client

    def extract(self, pdf_paths: List[str]) -> Any:
        raise NotImplementedError("Subclasses must implement extract()")
