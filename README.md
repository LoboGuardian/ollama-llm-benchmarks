# ollama-llm-benchmarks

Python-based tool for benchmarking local Large Language Models (LLMs) served via Ollama. This project systematically measures key performance indicators (**latency**, **throughput**) and resource utilization (**CPU**, **RAM**, **Temperature**) to inform model deployment and selection.

## Features

  * **Model Agnostic:** Dynamically queries and benchmarks any model listed by the local `ollama list` command.
  * **Performance Metrics:** Accurately measures time-to-first-token (**TTFT**), tokens-per-second (**T/s**), and total response latency.
  * **Hardware Monitoring (Platform-Aware):** Integrates deep system resource tracking using `psutil` and platform-specific tools to monitor the host machine and the specific Ollama process ID (**PID**).
  * **Structured Configuration:** Utilizes a `config.yaml` file to define models, prompts, and iteration counts, keeping logic separate from configuration.
  * **Clean Architecture:** Code is organized into distinct Python modules (e.g., `OllamaClient`, `ResourceMonitor`).
  * **Automated Reporting:** Generates a structured output (JSON/CSV) for easy data analysis and comparison between model runs.

## Quick Start

### Prerequisites

Ensure the following are installed and running on your host machine:

  * **Python 3.10+**
  * **Ollama Server:** Installed and running locally (`ollama serve`).
  * **Required Models:** Models must be pulled locally (e.g., `ollama pull deepseek-r1`).

### Installation and Setup

We recommend using **Poetry** for isolated dependency management.

```bash
# 1. Clone the repository
git clone https://github.com/LoboGuardian/ollama-llm-benchmarks.git
cd ollama-llm-benchmarks

# 2. Install dependencies (Requires 'pip install poetry' if not present)
poetry install

# 3. Activate the virtual environment
poetry shell
```

### Configuration (`config.yaml`)

Define your benchmarking parameters in `config.yaml`:

```yaml
# config.yaml example
models_to_test:
  - deepseek-r1:latest
  - qwen3:latest
  - mistral:latest

test_prompt: "Explain the Liskov Substitution Principle in the context of Python inheritance, providing a brief, non-trivial example."
iterations: 5
```

### Usage

Run the main orchestrator script to execute the benchmark against all configured models and prompts.

```bash
python benchmark_runner.py
```

## Project Structure

The codebase is modularized to adhere to **SOLID principles**, ensuring high cohesion and low coupling.

```
ollama-llm-benchmarks/
├── benchmark_runner.py      # Main Orchestrator
├── config.yaml              # Global Configuration File
├── llm_client.py            # Ollama API Handler
├── resource_monitor.py      # System/Process Monitoring
├── report_generator.py      # Data Aggregation & Output
└── pyproject.toml           # Poetry dependency file
```

# Understanding the Metrics

## Latency Metrics (User Experience)

Latency metrics measure the time it takes to get a response and are critical for perceived responsiveness, especially in interactive applications like chatbots.

### 1. Time-to-First-Token (TTFT)

* **What it Measures:** The time elapsed from when the request is sent to the Ollama server until the **very first token** of the response is received by the client.
* **Why it Matters:** This is the most crucial metric for **perceived responsiveness**. A low TTFT makes the LLM feel "snappy" because the user sees the output starting almost immediately.
    * **Calculation:** $\text{TTFT} = \text{Time of First Token Received} - \text{Time of Request Sent}$
    * **Phases Included:** The TTFT includes the time taken for the server to queue the request, load the model (if it wasn't pre-loaded), and **process the entire input prompt** (**Prefill Stage**).

---

### 2. Total Latency

* **What it Measures:** The total time elapsed from when the request is sent until the **final token** of the complete response is received.
* **Why it Matters:** This is the **end-to-end (E2E) time** for the whole task. It tells you how long the user waits for the *entire* answer. A fast TTFT followed by a slow generation rate can still result in high total latency and a frustrating experience.
    * **Calculation:** $\text{Total Latency} = \text{Time of Final Token Received} - \text{Time of Request Sent}$
    * **Relationship to TTFT:** $\text{Total Latency} = \text{TTFT} + \text{Generation Time}$ (where Generation Time is the time for all subsequent tokens).

---

## Throughput Metric (System Capacity)

Throughput measures the model's processing speed once it starts generating the response, indicating the raw efficiency and capacity of the serving system.

### 3. Tokens Per Second (T/s)

* **What it Measures:** The average rate at which the model generates output tokens over the entire response time. This is often referred to as **throughput**.
* **Why it Matters:** A higher T/s value means the model can generate text **faster**. This directly impacts the total latency (for long outputs) and the number of concurrent requests the server can handle.
    * **Calculation:** $\text{Tokens Per Second (T/s)} = \frac{\text{Total Tokens Generated}}{\text{Total Latency (in seconds)}}$
    * **Note:** This calculation provides the **overall** T/s for a single request, including the prompt processing time (TTFT). Sometimes benchmarks calculate **output T/s** by excluding the TTFT to focus purely on the decoding speed, but using **Total Latency** gives a more honest representation of the end-user's experience.

---

## Resource Metrics (Efficiency & Cost)

These metrics provide context for the latency and throughput numbers, linking model performance directly to the host machine's utilization.

| Metric | What it Measures | Why it Matters |
| :--- | :--- | :--- |
| **Ollama Process CPU %** | The percentage of CPU resources consumed by the specific Ollama server process during the benchmark run. | **Resource Scaling:** Identifies if the model is **CPU-bound**. High usage suggests you might need a faster CPU or a different model quantization. |
| **Ollama Process RAM (RSS) GB** | The Resident Set Size (RSS)—the physical memory (RAM) used by the Ollama process. | **Deployment Feasibility:** Determines the memory footprint. The **peak** RSS recorded indicates the minimum RAM required to run that specific model. |
| **System Temperature (°C)** | The host machine's CPU/GPU temperature. | **Thermal Throttling:** High temperatures can cause the hardware to slow down (**thermal throttling**), directly impacting latency and T/s. |
| **System CPU/RAM %** | The overall utilization of the host machine (system-wide). | **Contention:** Helps confirm if high Ollama resource usage is monopolizing the host system or if other background processes are interfering with the benchmark. |

By analyzing these three categories of metrics together, you get a complete picture of which model not only *responds quickly* (low TTFT) but also *generates efficiently* (high T/s) and *runs economically* on your hardware (low resource usage).