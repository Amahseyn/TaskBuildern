import json
import argparse
import sys

def calculate_accuracy(ground_truth_data, predicted_data):
    """
    Calculates a simple accuracy score based on exact matching of 
    important estimation fields (scopes, project summary, key signals).
    """
    total_checks = 0
    passed_checks = 0
    
    gt_summary = ground_truth_data.get("projectSummary", {})
    pred_summary = predicted_data.get("projectSummary", {})
    for key in ["type", "floors"]:
        total_checks += 1
        
        pred_val = pred_summary.get(key)
        if isinstance(pred_val, dict) and "value" in pred_val:
            pred_val = pred_val.get("value")
            
        if str(gt_summary.get(key)).lower() == str(pred_val).lower():
            passed_checks += 1

    gt_scopes = set(ground_truth_data.get("detectedScopes", []))
    pred_scopes = set(predicted_data.get("detectedScopes", []))
    
    for scope in gt_scopes:
        total_checks += 1
        if scope in pred_scopes:
            passed_checks += 1
            
    for scope in pred_scopes:
        if scope not in gt_scopes:
            total_checks += 1

    gt_signals = ground_truth_data.get("keySignals", {})
    pred_signals = predicted_data.get("keySignals", {})
    for key in ["hasExtension", "hasStructuralChanges"]:
        total_checks += 1
        
        pred_val = pred_signals.get(key)
        if isinstance(pred_val, dict) and "value" in pred_val:
            pred_val = pred_val.get("value")
            
        if gt_signals.get(key) == pred_val:
            passed_checks += 1

    accuracy = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    return accuracy, passed_checks, total_checks

def evaluate_run(ground_truth_path, predicted_path):
    with open(ground_truth_path, "r") as f:
        ground_truth = json.load(f)["data"]
        
    with open(predicted_path, "r") as f:
        prediction_json = json.load(f)
        
    metadata = prediction_json.get("metadata", {})
    predicted_data = prediction_json.get("data", {})
    
    accuracy, passed, total = calculate_accuracy(ground_truth, predicted_data)
    latency = metadata.get("latency_seconds", "Unknown")
    cost_usd = metadata.get("cost_usd", "Unknown")
    input_tokens = metadata.get("input_tokens", "Unknown")
    output_tokens = metadata.get("output_tokens", "Unknown")
    approach = metadata.get("approach", "Unknown")
    
    print("=" * 40)
    print(f"EVALUATION REPORT")
    print("=" * 40)
    print(f"Approach:      {approach}")
    print(f"Accuracy:      {accuracy:.2f}% ({passed}/{total} key checks passed)")
    print(f"Latency:       {latency} seconds")
    print(f"Cost (USD):    ${cost_usd}")
    print(f"Input Tokens:  {input_tokens}")
    print(f"Output Tokens: {output_tokens}")
    print("=" * 40)

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
