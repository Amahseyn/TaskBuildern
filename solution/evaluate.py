import json
import argparse
import sys
import math

def extract_value(val):
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val

def compare_values(gt_val, pred_val):
    if gt_val is None and pred_val is None:
        return True
    if gt_val is None or pred_val is None:
        return False
        
    if isinstance(gt_val, (int, float)) and isinstance(pred_val, (int, float)):
        return math.isclose(gt_val, pred_val, rel_tol=0.05)
        
    if isinstance(gt_val, str) and isinstance(pred_val, str):
        return gt_val.strip().lower() == pred_val.strip().lower()
        
    return str(gt_val).lower() == str(pred_val).lower()

def calculate_accuracy(ground_truth_data, predicted_data):
    results = {
        "summary": {"passed": 0, "total": 0},
        "scopes": {"passed": 0, "total": 0},
        "signals": {"passed": 0, "total": 0},
        "overall": {"passed": 0, "total": 0}
    }
    
    # 1. Evaluate Project Summary
    gt_summary = ground_truth_data.get("projectSummary", {})
    pred_summary = predicted_data.get("projectSummary", {})
    
    for key, gt_val in gt_summary.items():
        results["summary"]["total"] += 1
        pred_val = extract_value(pred_summary.get(key))
        if compare_values(gt_val, pred_val):
            results["summary"]["passed"] += 1

    # 2. Evaluate Scopes (Set Logic)
    gt_scopes = set(ground_truth_data.get("detectedScopes", []))
    pred_scopes = set([extract_value(s) for s in predicted_data.get("detectedScopes", [])])
    
    # Each scope in ground truth is a check
    for scope in gt_scopes:
        results["scopes"]["total"] += 1
        if scope in pred_scopes:
            results["scopes"]["passed"] += 1
            
    # Penalize for hallucinations (extra scopes not in ground truth)
    for scope in pred_scopes:
        if scope not in gt_scopes:
            results["scopes"]["total"] += 1

    # 3. Evaluate Key Signals
    gt_signals = ground_truth_data.get("keySignals", {})
    pred_signals = predicted_data.get("keySignals", {})
    
    for key, gt_val in gt_signals.items():
        results["signals"]["total"] += 1
        pred_val = extract_value(pred_signals.get(key))
        if compare_values(gt_val, pred_val):
            results["signals"]["passed"] += 1

    # 4. Overall Tally
    for category in ["summary", "scopes", "signals"]:
        results["overall"]["passed"] += results[category]["passed"]
        results["overall"]["total"] += results[category]["total"]

    def calc_pct(passed, total):
        return (passed / total) * 100 if total > 0 else 0

    scores = {
        "summary_pct": calc_pct(results["summary"]["passed"], results["summary"]["total"]),
        "scopes_pct": calc_pct(results["scopes"]["passed"], results["scopes"]["total"]),
        "signals_pct": calc_pct(results["signals"]["passed"], results["signals"]["total"]),
        "overall_pct": calc_pct(results["overall"]["passed"], results["overall"]["total"]),
        "passed": results["overall"]["passed"],
        "total": results["overall"]["total"]
    }
    
    return scores

def evaluate_run(ground_truth_path, predicted_path):
    with open(ground_truth_path, "r") as f:
        ground_truth = json.load(f)["data"]
        
    with open(predicted_path, "r") as f:
        prediction_json = json.load(f)
        
    metadata = prediction_json.get("metadata", {})
    predicted_data = prediction_json.get("data", {})
    
    scores = calculate_accuracy(ground_truth, predicted_data)
    
    latency = metadata.get("latency_seconds", "Unknown")
    cost_usd = metadata.get("cost_usd", "Unknown")
    input_tokens = metadata.get("input_tokens", "Unknown")
    output_tokens = metadata.get("output_tokens", "Unknown")
    approach = metadata.get("approach", "Unknown")
    
    print("=" * 50)
    print(f"EVALUATION REPORT: {approach.upper()}")
    print("=" * 50)
    print(f"Overall Accuracy:  {scores['overall_pct']:.2f}% ({scores['passed']}/{scores['total']} checks passed)")
    print(f" ├─ Summary Match: {scores['summary_pct']:.2f}%")
    print(f" ├─ Scopes Match:  {scores['scopes_pct']:.2f}%")
    print(f" └─ Signals Match: {scores['signals_pct']:.2f}%")
    print("-" * 50)
    print(f"Latency:           {latency} seconds")
    print(f"Cost (USD):        ${cost_usd}")
    print(f"Input Tokens:      {input_tokens}")
    print(f"Output Tokens:     {output_tokens}")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Extraction Accuracy and Latency")
    parser.add_argument("--gt", default="ground_truth.json", help="Path to ground truth JSON")
    parser.add_argument("--pred", required=True, help="Path to prediction JSON")
    args = parser.parse_args()
    
    try:
        evaluate_run(args.gt, args.pred)
    except Exception as e:
        print(f"Error evaluating: {e}")
        sys.exit(1)
