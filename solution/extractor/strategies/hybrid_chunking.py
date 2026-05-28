import os
from pathlib import Path
from typing import List, Any
import fitz

from extractor.logger import log
from extractor.prompts import SYSTEM_PROMPT
from extractor.strategies.base import BaseStrategy

class HybridChunkingStrategy(BaseStrategy):
    """Score pages by keyword density, pass only high-signal pages. Lowest token cost."""
    def extract(self, pdf_paths: List[str]) -> Any:
        log.info("━━ [hybrid_chunking] Hybrid Chunking with Keyword Scoring ━━")
        WEIGHTS = {
            "schedule": 3, "floor plan": 3, "area": 3, "gfa": 4, "gross floor": 4,
            "section": 2, "detail": 2, "specification": 3, "energy": 2, "nathers": 3,
            "footing": 3, "slab": 3, "framing": 3, "roof": 2, "insulation": 3,
            "window": 2, "door": 2, "demolish": 3, "retaining": 3, "structural": 2,
        }
        scored = []
        for path in pdf_paths:
            if not os.path.exists(path):
                log.warning("  Skipping missing: %s", path)
                continue
            try:
                doc = fitz.open(path)
                log.info("  Scoring %d pages in %s…", len(doc), Path(path).name)
                for i, page in enumerate(doc):
                    t = page.get_text()
                    tl = t.lower()
                    score = sum(w for kw, w in WEIGHTS.items() if kw in tl)
                    if i < 3:
                        score += 5  # always include first 3 pages
                    scored.append((score, i + 1, Path(path).name, t))
                doc.close()
            except Exception as e:
                log.error("  Error reading %s: %s", path, e)

        scored.sort(key=lambda x: x[0], reverse=True)
        filtered, limit, count = "", 500_000, 0
        for score, pnum, fname, text in scored:
            if len(filtered) + len(text) > limit:
                break
            filtered += f"\n--- [{fname}] Page {pnum} (score={score}) ---\n{text}"
            count += 1

        log.info("  Selected %d/%d pages, %s chars → LLM…", count, len(scored), f"{len(filtered):,}")
        prompt = f"{SYSTEM_PROMPT}\n\n=== FILTERED DOCUMENT TEXT ===\n{filtered}"
        return self.client.call([prompt])
