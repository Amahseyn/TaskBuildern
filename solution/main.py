#!/usr/bin/env python3
"""
Construction PDF Extraction Service
====================================
Extracts structured estimation signals from construction PDFs using 7 distinct
architectural approaches, from native multimodal to two-pass self-verification.

Usage:
    python main.py <pdf1> [pdf2 ...] --approach native_multimodal --model gemini-3.5-flash
"""

import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

from extractor import setup_logging, log, LLMClient, STRATEGIES


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Construction PDF Extraction Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(
            f"  {k}: {v.__doc__.strip().splitlines()[0] if v.__doc__ else ''}"
            for k, v in STRATEGIES.items()
        ),
    )
    parser.add_argument("pdfs", nargs="+", help="Path(s) to the PDF file(s)")
    parser.add_argument(
        "--approach", choices=list(STRATEGIES.keys()), default="native_multimodal",
        help="Extraction approach to use (default: native_multimodal)",
    )
    parser.add_argument(
        "--model", default="gemini-3.5-flash",
        help="Gemini model to use (default: gemini-3.5-flash)",
    )
    parser.add_argument(
        "-o", "--output", default="estimation_signals.json",
        help="Output JSON file path (default: estimation_signals.json)",
    )
    parser.add_argument(
        "--log-file", default=None,
        help="Optional path to write full logs to a file",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable DEBUG-level logging",
    )
    args = parser.parse_args()

    # Re-initialize logging with user prefs
    setup_logging(verbose=args.verbose, log_file=args.log_file)

    log.info("=" * 60)
    log.info("  Approach : %s", args.approach)
    log.info("  Model    : %s", args.model)
    log.info("  PDFs     : %s", ", ".join(Path(p).name for p in args.pdfs))
    log.info("  Output   : %s", args.output)
    log.info("=" * 60)

    try:
        client = LLMClient(model_name=args.model)
    except Exception as e:
        log.error("Initialization failed: %s", e)
        sys.exit(1)

    strategy_cls = STRATEGIES[args.approach]
    strategy = strategy_cls(client=client)

    start = time.time()
    try:
        response = strategy.extract(args.pdfs)
    except Exception as e:
        log.error("Extraction failed: %s", e)
        sys.exit(1)
    latency = time.time() - start

    if not response:
        log.error("No response received from Gemini.")
        sys.exit(1)

    in_tok  = response.usage_metadata.prompt_token_count
    out_tok = response.usage_metadata.candidates_token_count
    cost    = client.calculate_cost(in_tok, out_tok)

    try:
        data = json.loads(response.text)
    except Exception as e:
        log.error("Failed to parse JSON response: %s", e)
        data = {"raw_text": response.text}

    output = {
        "metadata": {
            "approach": args.approach,
            "approach_description": strategy_cls.__doc__.strip().splitlines()[0] if strategy_cls.__doc__ else "",
            "model": args.model,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "latency_seconds": round(latency, 2),
            "cost_usd": round(cost, 6),
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "pdfs": [str(p) for p in args.pdfs],
        },
        "data": data,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    log.info("=" * 60)
    log.info("  ✓ Saved  : %s", args.output)
    log.info("  Latency  : %.2f seconds", latency)
    log.info("  Tokens   : %d in / %d out", in_tok, out_tok)
    log.info("  Cost     : $%.6f USD", cost)
    log.info("=" * 60)

if __name__ == "__main__":
    main()
