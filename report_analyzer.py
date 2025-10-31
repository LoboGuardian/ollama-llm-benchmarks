import json
from typing import Dict, Any, List
from collections import defaultdict
from tabulate import tabulate # External dependency for clean output

# --- Data Ingestion (SRP) ---
def load_report(file_path: str) -> Dict[str, Any]:
    """Loads and returns the JSON content of the benchmark report."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Report file not found at '{file_path}'.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{file_path}'. Check file integrity.")
        exit(1)

# --- Analysis Logic (DRY) ---
def analyze_resource_usage(raw_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, float]]:
    """
    Calculates the maximum observed resource usage (CPU/RAM) across all runs for each model.
    This logic adheres to the DRY principle by iterating over the structured data once.
    """
    model_max_resources = defaultdict(lambda: {
        "max_system_cpu": 0.0,
        "max_ollama_cpu": 0.0,
        "max_ollama_ram_gb": 0.0
    })

    for model, runs in raw_results.items():
        for run in runs:
            # We are interested in the *peak* usage during the LLM call, so we check both snapshots.
            for snapshot in run.get('resource_snapshots', []):
                # System CPU % (Host impact)
                model_max_resources[model]["max_system_cpu"] = max(
                    model_max_resources[model]["max_system_cpu"],
                    snapshot.get('system_cpu_percent', 0.0)
                )

                # Ollama Process CPU % (Specific load)
                model_max_resources[model]["max_ollama_cpu"] = max(
                    model_max_resources[model]["max_ollama_cpu"],
                    snapshot.get('ollama_process_cpu_percent', 0.0)
                )

                # Ollama Process RAM RSS (Memory footprint)
                model_max_resources[model]["max_ollama_ram_gb"] = max(
                    model_max_resources[model]["max_ollama_ram_gb"],
                    snapshot.get('ollama_process_ram_rss_gb', 0.0)
                )
                
    # Cast back to a standard dict for cleaner output
    return dict(model_max_resources) 

# --- New Utility Function (SRP/DRY) ---
def format_memory_usage(gb_value: float) -> str:
    """Converts a GB value into a formatted string showing both GB and MB."""
    # Guard against zero or negative values
    if gb_value <= 0:
        return "0.00 GB (0 MB)"
    
    # Calculate MB (1 GB = 1024 MB)
    mb_value = gb_value * 1024
    
    # Return formatted string
    return f"{gb_value:.2f} GB ({int(mb_value)} MB)"

# --- Reporting (Interface Segregation Principle - ISP) ---
def generate_summary_report(report_data: Dict[str, Any]):
    """Generates and prints a human-readable summary table and resource analysis."""
    
    print("\n" + "="*80)
    print("LLM Benchmark Analysis Report")
    print("="*80)
    
    # 1. Performance Summary Table
    print("\n### Performance Summary (Averages)\n")
    summary_data = report_data.get('summary_by_model', {})
    
    table_headers = [
        "Model", "Runs", "Latency (s)", "TTFT (s)", "Tokens/s"
    ]
    
    table_rows = []
    for model, metrics in summary_data.items():
        table_rows.append([
            model,
            metrics.get('total_runs'),
            f"{metrics.get('total_latency_s'):.4f}",
            f"{metrics.get('time_to_first_token_s'):.4f}",
            f"{metrics.get('tokens_per_second'):.2f}"
        ])

    print(tabulate(table_rows, headers=table_headers, tablefmt="fancy_grid"))
    
    # 2. Resource Usage Analysis
    print("\n" + "-"*80)
    print("### Peak Resource Usage\n")
    raw_results = report_data.get('raw_results', {})
    max_resources = analyze_resource_usage(raw_results)

    resource_headers = [
        "Model", "Max Host CPU (%)", "Max Ollama CPU (%)", "**Max Ollama RAM (GB/MB)**" # Updated header
    ]

    resource_rows = []
    for model, res_metrics in max_resources.items():
        # Use the new utility function here
        formatted_ram = format_memory_usage(res_metrics['max_ollama_ram_gb'])
        
        resource_rows.append([
            model,
            f"{res_metrics['max_system_cpu']:.1f}",
            f"{res_metrics['max_ollama_cpu']:.1f}",
            formatted_ram # Insert the formatted string
        ])
    
    print(tabulate(resource_rows, headers=resource_headers, tablefmt="fancy_grid"))

    print("\n" + "="*80)


if __name__ == "__main__":
    # The default output from benchmark_runner.py is 'benchmark_results.json'
    REPORT_FILE = "benchmark_results.json" 
    
    report = load_report(REPORT_FILE)
    generate_summary_report(report)