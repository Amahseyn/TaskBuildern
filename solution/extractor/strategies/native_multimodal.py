import os
from pathlib import Path
from typing import List, Any
import google.generativeai as genai

from extractor.logger import log
from extractor.prompts import SYSTEM_PROMPT
from extractor.strategies.base import BaseStrategy

import concurrent.futures

class NativeMultimodalStrategy(BaseStrategy):
    """Upload raw PDFs to Gemini File API. Best accuracy; Gemini reads text+visuals."""
    def extract(self, pdf_paths: List[str]) -> Any:
        log.info("━━ [native_multimodal] Native Multimodal via Gemini File API ━━")
        valid = [p for p in pdf_paths if os.path.exists(p)]
        if not valid:
            raise FileNotFoundError("No valid PDF paths provided.")

        def _upload(path: str):
            mb = Path(path).stat().st_size / 1_048_576
            log.info("  ↑ Uploading: %s (%.2f MB)", Path(path).name, mb)
            return genai.upload_file(path=path)

        uploaded = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            uploaded = list(executor.map(_upload, valid))

        log.info("  ⏳ Waiting for Gemini to process %d file(s)…", len(uploaded))
        self.client.wait_for_files(uploaded)
        log.info("  ✓ All files active. Running extraction…")

        def _delete(f):
            try:
                genai.delete_file(f.name)
                log.debug("  🗑  Deleted: %s", f.name)
            except Exception as e:
                log.warning("  Could not delete %s: %s", f.name, e)

        try:
            return self.client.call(uploaded + [SYSTEM_PROMPT])
        finally:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                executor.map(_delete, uploaded)
