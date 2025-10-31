# report_generator.py
import json
from datetime import datetime

class ReportGenerator:
    """
    Handles data aggregation, calculation of final averages, and output to file (SRP).
    """
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.results = {}

    def add_result(self, model_name: str, iteration_data: dict, resources_data: list):
        """
        Adds a complete benchmark run (LLM metrics + resource snapshots) to the results.
        """
        if model_name not in self.results:
            self.results[model_name] = []
        
        # Combine data into a single, comprehensive iteration entry
        combined_data = {
            "run_timestamp": datetime.now().isoformat(),
            "llm_metrics": iteration_data,
            "resource_snapshots": resources_data
        }
        self.results[model_name].append(combined_data)

    def _calculate_averages(self, model_name: str) -> dict:
        """
        Calculates aggregate statistics across all iterations for a model (DRY).
        """
        runs = self.results.get(model_name, [])
        if not runs:
            return {}

        avg_metrics = {
            "total_latency_s": 0.0,
            "time_to_first_token_s": 0.0,
            "tokens_per_second": 0.0,
            "total_runs": len(runs)
        }

        for run in runs:
            metrics = run['llm_metrics']
            avg_metrics["total_latency_s"] += metrics["total_latency_s"]
            avg_metrics["time_to_first_token_s"] += metrics["time_to_first_token_s"]
            avg_metrics["tokens_per_second"] += metrics["tokens_per_second"]

        for key in avg_metrics:
            if key != "total_runs":
                avg_metrics[key] = round(avg_metrics[key] / avg_metrics["total_runs"], 4)
                
        # To keep this focused, we omit complex resource averaging, but in a real-world scenario,
        # you'd also average peak/median resource usage here.
        return avg_metrics


    def finalize_report(self):
        """
        Generates final summaries and writes the entire report to a JSON file.
        """
        final_report = {
            "metadata": {
                "report_generated": datetime.now().isoformat(),
                "test_models": list(self.results.keys())
            },
            "summary_by_model": {},
            "raw_results": self.results
        }
        
        for model in self.results:
            final_report["summary_by_model"][model] = self._calculate_averages(model)

        with open(self.output_path, 'w') as f:
            # Use indent for human-readable JSON output (Clean Code)
            json.dump(final_report, f, indent=4)
        
        print(f"\nReport successfully written to: {self.output_path}")
