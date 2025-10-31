# benchmark_runner.py
import yaml
import time
from llm_client import OllamaClient
from resource_monitor import ResourceMonitor
from report_generator import ReportGenerator

# --- Configuration Loader ---
def load_config(path: str = "config.yaml") -> dict:
    """Loads and validates configuration from the YAML file."""
    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Basic Validation (Clean Code/Fail Fast)
        required_keys = ['models_to_test', 'test_prompt', 'iterations', 'output_file', 'ollama_host']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Configuration key '{key}' is missing in config.yaml")
        
        return config
    except FileNotFoundError:
        print(f"Error: config.yaml not found at {path}. Aborting.")
        exit(1)
    except Exception as e:
        print(f"Error loading config: {e}. Aborting.")
        exit(1)

# --- Main Execution Logic ---
def run_benchmark():
    """Coordinates the LLM and Resource Monitoring runs."""
    print("--- Starting LLM Benchmarking Suite ---")
    config = load_config()

    # DIP: Instantiate the clients based on config
    llm_client = OllamaClient(host=config['ollama_host'])
    monitor = ResourceMonitor()
    reporter = ReportGenerator(output_path=config['output_file'])

    for model in config['models_to_test']:
        print(f"\n[MODEL: {model}] Starting {config['iterations']} iterations...")
        
        for i in range(1, config['iterations'] + 1):
            print(f"  -> Run {i}/{config['iterations']}: Sending prompt...")
            
            # 1. Run the LLM Generation
            # We don't want the monitor to interfere with LLM timing, 
            # so we run it in the background or during the LLM's run time.
            
            resource_snapshots = []
            
            # Capture initial snapshot
            resource_snapshots.append(monitor.get_resource_snapshot())
            
            # Start LLM Generation
            llm_metrics = llm_client.generate_response(
                model=model, 
                prompt=config['test_prompt']
            )
            
            # Capture final snapshot (post-inference)
            resource_snapshots.append(monitor.get_resource_snapshot())

            print(f"     Metrics: Latency={llm_metrics['total_latency_s']}s, T/s={llm_metrics['tokens_per_second']}")
            
            # 2. Add results to the reporter
            reporter.add_result(model, llm_metrics, resource_snapshots)
            
            # Small delay between runs (DRY)
            time.sleep(1) 
            
    # 3. Finalize and save the report
    reporter.finalize_report()
    print("--- Benchmarking Complete ---")


if __name__ == "__main__":
    run_benchmark()

# Principle-Based Rationale (PBR):
# The `run_benchmark` function is an orchestrator, adhering to the **DRY** principle 
# by looping through models and iterations, rather than repeating logic. It uses the 
# instantiated classes (`llm_client`, `monitor`, `reporter`) as dependencies, fulfilling 
# the **Dependency Inversion Principle (DIP)**. The logic for resource sampling is placed 
# immediately before and after the critical LLM call to capture the peak load interval.