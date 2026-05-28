import json
from typing import List, Any

from extractor.logger import log
from extractor.strategies.base import BaseStrategy
from extractor.strategies.native_multimodal import NativeMultimodalStrategy

class SelfVerificationStrategy(BaseStrategy):
    """
    Pass 1: Multimodal extraction (v1). Pass 2: LLM reviews its own output,
    checks internal consistency, and self-corrects. Highest reliability; 2× cost.
    """
    def extract(self, pdf_paths: List[str]) -> Any:
        log.info("━━ [self_verification] Chain-of-Thought Self-Verification (Two-Pass) ━━")
        log.info("  ── Pass 1: Initial Multimodal Extraction ──")
        v1_strategy = NativeMultimodalStrategy(self.client)
        r1 = v1_strategy.extract(pdf_paths)
        try:
            d1 = json.loads(r1.text)
        except Exception as e:
            log.error("  Pass 1 parse failed: %s", e)
            raise

        log.info("  ── Pass 2: LLM Self-Verification & Correction ──")
        verify_prompt = f"""You are a QA reviewer for a construction estimation AI.

Below is an initial extraction (Pass 1). Your tasks:
1. Check INTERNAL CONSISTENCY (e.g., floors=2 but no upper floor plan detected).
2. Check CROSS-DOCUMENT CONSISTENCY (energy report GFA vs. drawing area schedule).
3. Verify detectedScopes — assert NO scope without clear evidence.
4. Verify keySignals — confirm hasExtension aligns with floor plan.
5. Correct any inconsistent or unsupported field.

=== PASS 1 EXTRACTION ===
{json.dumps(d1, indent=2)}

=== VERIFICATION RULES ===
- CONFIRMED correct → keep value/confidence/reasoning unchanged.
- CORRECTED → update value, set confidence="low", prefix reasoning with "[CORRECTED] ".
- UNCERTAIN → set value=null, confidence="low", prefix reasoning with "[UNCERTAIN] ".
- Return a valid ExtractionResult JSON. Do NOT omit any field."""

        log.info("  Sending Pass 1 result for self-verification…")
        response = self.client.call([verify_prompt], temperature=0.1)
        log.info("  ✓ Self-verification complete.")
        return response
