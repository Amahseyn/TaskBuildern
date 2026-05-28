import os
from pathlib import Path
from typing import List, Any
from pdf2image import convert_from_path

from extractor.logger import log
from extractor.prompts import SYSTEM_PROMPT
from extractor.strategies.base import BaseStrategy

class VisionVLMStrategy(BaseStrategy):
    """Convert pages to PIL images and send directly to vision model. High accuracy, high cost."""
    def extract(self, pdf_paths: List[str]) -> Any:
        log.info("━━ [vision_vlm] Vision VLM — Image Payload (pdf2image) ━━")
        images = []
        for path in pdf_paths:
            if not os.path.exists(path):
                log.warning("  Skipping missing: %s", path)
                continue
            try:
                log.info("  Converting %s at 150 DPI…", Path(path).name)
                imgs = convert_from_path(path, dpi=150)
                images.extend(imgs)
                log.info("  Got %d image(s).", len(imgs))
            except Exception as e:
                log.error("  Error converting %s: %s", path, e)

        if not images:
            raise RuntimeError("No images extracted from PDFs.")
        log.warning("  Sending %d raw images — expect high token usage!", len(images))
        return self.client.call(images + [SYSTEM_PROMPT])
