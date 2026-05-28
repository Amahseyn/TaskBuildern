import os
import json
from pathlib import Path
from typing import List, Any
from pdf2image import convert_from_path

from extractor.logger import log
from extractor.prompts import SYSTEM_PROMPT
from extractor.strategies.base import BaseStrategy
from extractor.strategies.hybrid_chunking import HybridChunkingStrategy
from extractor.strategies.vision_vlm import VisionVLMStrategy

class TwoStageHybridStrategy(BaseStrategy):
    """
    Stage 1: Fast text extraction (v3). Stage 2: Vision escalation only for
    low-confidence/null fields. Best cost-accuracy tradeoff for production.
    """
    def extract(self, pdf_paths: List[str]) -> Any:
        log.info("━━ [two_stage] Two-Stage Hybrid: Text-First + Vision Escalation ━━")
        log.info("  ── Stage 1: Text Extraction ──")
        v3_strategy = HybridChunkingStrategy(self.client)
        r1 = v3_strategy.extract(pdf_paths)
        try:
            d1 = json.loads(r1.text)
        except Exception as e:
            log.error("  Stage 1 parse failed (%s). Falling back to vision_vlm.", e)
            v5_strategy = VisionVLMStrategy(self.client)
            return v5_strategy.extract(pdf_paths)

        low_conf = []
        for section, fields in d1.items():
            if isinstance(fields, dict):
                for fname, fval in fields.items():
                    if isinstance(fval, dict):
                        if fval.get("confidence") == "low" or fval.get("value") is None:
                            low_conf.append(f"{section}.{fname}")

        log.info("  Stage 1 done. Low-confidence fields: %s", low_conf or "none")
        if not low_conf:
            log.info("  All fields high-confidence. Skipping vision escalation.")
            return r1

        log.info("  ── Stage 2: Vision Escalation for %d field(s) ──", len(low_conf))
        esc_images = []
        for path in pdf_paths:
            if not os.path.exists(path):
                continue
            try:
                imgs = convert_from_path(path, dpi=120, first_page=1, last_page=6)
                esc_images.extend(imgs)
                log.info("  Added %d escalation image(s) from %s.", len(imgs), Path(path).name)
            except Exception as e:
                log.error("  Image conversion error for %s: %s", path, e)

        if not esc_images:
            log.warning("  No escalation images available. Returning Stage 1 result.")
            return r1

        escalation_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"=== STAGE 1 TEXT EXTRACTION ===\n{json.dumps(d1, indent=2)}\n\n"
            f"=== ESCALATION TASK ===\n"
            f"Low-confidence fields from Stage 1:\n{json.dumps(low_conf, indent=2)}\n\n"
            "Review the drawings and produce a COMPLETE corrected ExtractionResult JSON. "
            "Override low-confidence/null fields with values visible in the drawings. "
            "Retain all high-confidence Stage 1 values unchanged."
        )
        log.info("  Sending %d images + Stage 1 context to Gemini…", len(esc_images))
        response = self.client.call(esc_images + [escalation_prompt])
        log.info("  ✓ Stage 2 complete.")
        return response
