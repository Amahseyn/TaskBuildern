#!/usr/bin/env python3
"""
Run All Solutions and Evaluate
==============================
Executes all defined extraction strategies against the provided PDFs,
calculates accuracy metrics using ground truth, and saves the comprehensive
results to a single JSON report.

Usage:
    python run_all.py <pdf1> [pdf2 ...] --gt ground_truth.json
"""

import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

from extractor import setup_logging, log, LLMClient, STRATEGIES
from evaluate import calculate_accuracy

def main():
    parser = argparse.ArgumentParser(description="Run all extraction strategies and evaluate them.")
    parser.add_argument("pdfs", nargs="+", help="Path(s) to the PDF file(s)")
    parser.add_argument("--model", default="gemini-3.5-flash", help="Gemini model to use")
    parser.add_argument("--gt", default="ground_truth.json", help="Path to ground truth JSON")
    parser.add_argument("-o", "--output", default="all_solutions_report.json", help="Output JSON file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable DEBUG-level logging")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    try:
        with open(args.gt, "r") as f:
            ground_truth = json.load(f)["data"]
    except Exception as e:
        log.error(f"Failed to load ground truth: {e}")
        sys.exit(1)

    try:
        client = LLMClient(model_name=args.model)
    except Exception as e:
        log.error("Initialization failed: %s", e)
        sys.exit(1)

    final_report = {
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model": args.model,
            "pdfs": [str(p) for p in args.pdfs],
            "ground_truth_file": args.gt
        },
        "results": {}
    }

    for approach_name, strategy_cls in STRATEGIES.items():
        log.info("=" * 60)
        log.info("  Running approach: %s", approach_name)
        log.info("=" * 60)

        strategy = strategy_cls(client=client)

        start = time.time()
        try:
            response = strategy.extract(args.pdfs)
            success = True
            error_msg = None
        except Exception as e:
            log.error("Extraction failed for %s: %s", approach_name, e)
            success = False
            error_msg = str(e)
            response = None
        
        latency = time.time() - start

        if success and response:
            try:
                in_tok  = response.usage_metadata.prompt_token_count
                out_tok = response.usage_metadata.candidates_token_count
                cost    = client.calculate_cost(in_tok, out_tok)
            except AttributeError:
                # Fallback if usage_metadata is missing
                in_tok, out_tok, cost = 0, 0, 0.0

            try:
                data = json.loads(response.text)
                accuracy, passed, total = calculate_accuracy(ground_truth, data)
                
                final_report["results"][approach_name] = {
                    "success": True,
                    "latency_seconds": round(latency, 2),
                    "cost_usd": round(cost, 6),
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "accuracy_percent": round(accuracy, 2),
                    "accuracy_details": f"{passed}/{total} key checks passed",
                    "extracted_data": data
                }
            except Exception as e:
                log.error("Failed to parse JSON response for %s: %s", approach_name, e)
                final_report["results"][approach_name] = {
                    "success": False,
                    "error": f"JSON parsing or evaluation failed: {e}",
                    "raw_output": response.text,
                    "latency_seconds": round(latency, 2)
                }
        else:
            final_report["results"][approach_name] = {
                "success": False,
                "error": error_msg,
                "latency_seconds": round(latency, 2)
            }

    with open(args.output, "w") as f:
        json.dump(final_report, f, indent=2)

    log.info("=" * 60)
    log.info("All approaches completed. Comprehensive report saved to: %s", args.output)
    log.info("=" * 60)

if __name__ == "__main__":
    main()
