import os
from pathlib import Path
from typing import List, Any
import google.generativeai as genai

from extractor.logger import log
from extractor.prompts import SYSTEM_PROMPT
from extractor.strategies.base import BaseStrategy

class NativeMultimodalStrategy(BaseStrategy):
    """Upload raw PDFs to Gemini File API. Best accuracy; Gemini reads text+visuals."""
    def extract(self, pdf_paths: List[str]) -> Any:
        log.info("━━ [native_multimodal] Native Multimodal via Gemini File API ━━")
        valid = [p for p in pdf_paths if os.path.exists(p)]
        if not valid:
            raise FileNotFoundError("No valid PDF paths provided.")

        uploaded = []
        for path in valid:
            mb = Path(path).stat().st_size / 1_048_576
            log.info("  ↑ Uploading: %s (%.2f MB)", Path(path).name, mb)
            f = genai.upload_file(path=path)
            uploaded.append(f)

        log.info("  ⏳ Waiting for Gemini to process %d file(s)…", len(uploaded))
        self.client.wait_for_files(uploaded)
        log.info("  ✓ All files active. Running extraction…")

        try:
            return self.client.call(uploaded + [SYSTEM_PROMPT])
        finally:
            for f in uploaded:
                try:
                    genai.delete_file(f.name)
                    log.debug("  🗑  Deleted: %s", f.name)
                except Exception as e:
                    log.warning("  Could not delete %s: %s", f.name, e)
