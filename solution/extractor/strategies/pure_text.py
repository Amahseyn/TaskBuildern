import os
from pathlib import Path
from typing import List, Any
import fitz

from extractor.logger import log
from extractor.prompts import SYSTEM_PROMPT
from extractor.strategies.base import BaseStrategy

class PureTextStrategy(BaseStrategy):
    """Extract raw text from all pages. Fastest & cheapest; fails on raster drawings."""
    def extract(self, pdf_paths: List[str]) -> Any:
        log.info("━━ [pure_text] Pure Text Extraction via PyMuPDF ━━")
        text, limit = "", 800_000
        for path in pdf_paths:
            if not os.path.exists(path):
                log.warning("  Skipping missing file: %s", path)
                continue
            try:
                doc = fitz.open(path)
                log.info("  Extracting %d pages from %s…", len(doc), Path(path).name)
                for i, page in enumerate(doc):
                    text += f"\n--- Page {i+1} ---\n{page.get_text()}"
                    if len(text) >= limit:
                        log.warning("  Char limit hit at page %d. Truncating.", i+1)
                        break
                doc.close()
            except Exception as e:
                log.error("  Error reading %s: %s", path, e)

        log.info("  Text length: %s chars → sending to LLM…", f"{len(text):,}")
        return self.client.call([f"{SYSTEM_PROMPT}\n\n=== DOCUMENT TEXT ===\n{text[:limit]}"])
