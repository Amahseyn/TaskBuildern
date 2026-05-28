import os
from pathlib import Path
from typing import List, Any
from pdf2image import convert_from_path
import pytesseract

from extractor.logger import log
from extractor.prompts import SYSTEM_PROMPT
from extractor.strategies.base import BaseStrategy

class OCRPipelineStrategy(BaseStrategy):
    """Rasterize pages, run Tesseract OCR locally. Good for scanned/raster PDFs."""
    def extract(self, pdf_paths: List[str]) -> Any:
        log.info("━━ [ocr_pipeline] OCR Pipeline (pdf2image + Tesseract) ━━")
        text, limit = "", 500_000
        for path in pdf_paths:
            if not os.path.exists(path):
                log.warning("  Skipping missing: %s", path)
                continue
            try:
                log.info("  Rasterizing %s at 200 DPI…", Path(path).name)
                images = convert_from_path(path, dpi=200)
                log.info("  Running OCR on %d page(s)…", len(images))
                for i, img in enumerate(images):
                    log.debug("    OCR page %d/%d…", i+1, len(images))
                    ocr = pytesseract.image_to_string(img, config="--oem 3 --psm 6 -l eng")
                    text += f"\n--- Page {i+1} ---\n{ocr}"
                    if len(text) >= limit:
                        log.warning("  Char limit hit at page %d.", i+1)
                        break
            except Exception as e:
                log.error("  Error processing %s: %s", path, e)

        log.info("  OCR done: %s chars → LLM…", f"{len(text):,}")
        return self.client.call([f"{SYSTEM_PROMPT}\n\n=== OCR TEXT ===\n{text[:limit]}"])
