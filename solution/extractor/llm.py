import os
import time
import logging
from typing import Any
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

from extractor.schemas import ExtractionResult
from extractor.logger import log

MODEL_PRICING = {
    "gemini-3.1-pro":   {"input": 1.25,   "output": 10.00},
    "gemini-3.5-flash": {"input": 0.075,  "output": 0.30},
    "gemini-3-flash":   {"input": 0.075,  "output": 0.30},
    "gemini-3.1-flash-lite": {"input": 0.0375, "output": 0.15},
    "gemini-2.5-pro":   {"input": 1.25,   "output": 10.00},
    "gemini-2.5-flash": {"input": 0.075,  "output": 0.30},
}

class LLMClient:
    def __init__(self, model_name: str = "gemini-3.5-flash"):
        self.model_name = model_name
        self._setup()

    def _setup(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            log.critical("GEMINI_API_KEY is not set.")
            raise EnvironmentError("Export GEMINI_API_KEY before running.")
        genai.configure(api_key=api_key)
        log.info("✓ Gemini API configured | Model: %s", self.model_name)

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        p = MODEL_PRICING.get(self.model_name, {"input": 0.075, "output": 0.30})
        return (input_tokens / 1_000_000) * p["input"] + (output_tokens / 1_000_000) * p["output"]

    def make_model(self, temperature: float = 0.0) -> genai.GenerativeModel:
        return genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ExtractionResult,
                temperature=temperature,
            ),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        before_sleep=before_sleep_log(log, logging.WARNING),
        reraise=True,
    )
    def call(self, contents: list, temperature: float = 0.0) -> Any:
        log.debug("→ Sending request to %s…", self.model_name)
        model = self.make_model(temperature)
        response = model.generate_content(contents)
        in_tok  = response.usage_metadata.prompt_token_count
        out_tok = response.usage_metadata.candidates_token_count
        cost    = self.calculate_cost(in_tok, out_tok)
        log.debug("← Response: in=%d tok, out=%d tok, cost=$%.6f", in_tok, out_tok, cost)
        return response

    def wait_for_files(self, files: list) -> None:
        pending = list(files)
        while pending:
            next_pending = []
            for f in pending:
                info = genai.get_file(f.name)
                if info.state.name == "PROCESSING":
                    log.debug("  ⏳ Still processing: %s", f.name)
                    next_pending.append(f)
                elif info.state.name == "FAILED":
                    raise RuntimeError(f"File processing FAILED: {f.name}")
                else:
                    log.debug("  ✓ Ready: %s", f.name)
            if next_pending:
                time.sleep(3)
            pending = next_pending
