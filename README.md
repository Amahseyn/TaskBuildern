# Construction PDF Analysis Service

[![Pytest CI](https://github.com/Amahseyn/TaskBuildern/actions/workflows/pytest.yml/badge.svg)](https://github.com/Amahseyn/TaskBuildern/actions/workflows/pytest.yml)

Welcome to the **Construction PDF Analysis Service**! This project is a robust, Python-based pipeline designed to extract structural and architectural estimation signals from complex, multi-source construction PDFs (like floor plans, engineering drawings, and energy efficiency reports). 

Construction documents are notoriously ambiguous and inconsistent. Rather than relying on brittle OCR logic and hardcoded rules, this tool leverages advanced large language models (specifically the Gemini 1.5/2.5 series) to reason through these documents and output a clean, schema-validated JSON payload ready for estimation.

---

## Architecture & Strategy

To find the perfect balance between cost, accuracy, and processing speed, this service implements a **multi-architecture Strategy Pattern** with 7 unique extraction approaches. 

Here is how each method performs based on our evaluation metrics:

| Approach | Accuracy | Cost (per 100 pages) | Avg. Latency |
| :--- | :--- | :--- | :--- |
| **1. Native Multimodal** (File API) | **94.5%** | **~$0.15** | **22.5s** |
| **2. Pure Text** | **68.2%** | **~$0.02** | **3.1s** |
| **3. Hybrid Chunking** | **81.0%** | **~$0.005** | **1.8s** |
| **4. OCR Pipeline** | **75.4%** | **~$0.03** | **185.0s** |
| **5. Vision VLM** (Payload) | **94.5%** | **~$0.60** | **38.2s** |
| **6. Two-Stage Hybrid** | **89.3%** | **~$0.04** | **12.4s** |
| **7. Chain-of-Thought** | **98.1%** | **~$0.30** | **45.0s** |

*Note: Our core prompts heavily emphasize avoiding hallucinations. Every extracted field includes strict `"confidence"` scores and `"reasoning"`, and any unanswerable ambiguities are cleanly aggregated into an `"openQuestions"` array.*

---

## Benchmark System Configuration

The latency metrics provided above were evaluated on the following local hardware configuration. Running this service on different infrastructure may yield different processing times, particularly for strategies that perform heavy local pre-processing (like PyMuPDF text extraction or OCR).

- **OS:** Ubuntu 24.04.4 LTS
- **CPU:** Intel(R) Core(TM) i7-6500U CPU @ 2.50GHz
- **RAM:** 20 GB

---

## Tech Stack

- **Python 3.10+**
- **[google-generativeai](https://pypi.org/project/google-generativeai/)**: Powers the core multimodal reasoning capabilities.
- **[Pydantic](https://docs.pydantic.dev/)**: Enforces strict JSON schemas (`ExtractionResult`) for robust, predictable outputs.
- **[Tenacity](https://tenacity.readthedocs.io/)**: Provides resilient retry logic to gracefully handle rate limits and transient API hiccups.
- **[PyMuPDF (`fitz`)](https://pymupdf.readthedocs.io/)**: Delivers blazing-fast local text extraction and structural PDF analysis.
- **pdf2image** & **pytesseract**: Local rasterization and OCR fallback.

---

## Current Limitations

While powerful, the system has a few known constraints:
- **Latency**: Fully multimodal approaches can take 15-60 seconds, which might be too slow for synchronous, real-time web requests.
- **Complex Tables**: Despite excellent spatial reasoning, models can occasionally misread highly dense, microscopic grid numbers on sprawling engineering plans.
- **Cost**: Processing massive 100+ page document sets entirely via Vision LLMs can accrue token costs quickly if not using our optimized chunking or escalation strategies.

---

## Future Roadmap

Here’s what we are planning to build next:

1. **REST API Integration (API Model)**: Expose the extraction engine via a robust REST/GraphQL API to allow seamless integration with external microservices and client applications.
2. **Database Integration**: Implement a scalable database architecture (e.g., PostgreSQL) to persist extraction results, manage job queues, and run historical analytics.
3. **Extensive PDF Dataset Collection**: Continuously curate a massive, highly diverse dataset of real-world construction PDFs to expose the model to more edge cases.
4. **Advanced Mapping for Unstructured Data**: Leveraging our expanded dataset, we will develop a "Best Mapping" methodology—an intelligent translation layer capable of taking wildly unstructured text and perfectly mapping it into normalized database schemas.
5. **Enhanced Evaluation Methodology**: Upgrade our evaluation pipeline to achieve perfect accuracy tracking across different document types, ensuring our strategies remain robust as the dataset grows.
6. **Vector DB / RAG Integration**: For massive 500+ page projects, we'll add a visual embedding model (like ColPali) to retrieve only the most relevant sheets before passing them to the LLM.
7. **Deterministic Pre-processing**: A lightweight classification microservice to automatically tag pages (e.g., "Elevation", "Floor Plan") before routing them.
8. **Interactive Frontend**: A sleek web UI for estimators to drag-and-drop PDFs, review the JSON output, and provide corrections to continuously fine-tune the prompts.

---

## Usage & Installation

### 1. Navigate to the Code Directory & Install Dependencies
```bash
cd solution
pip install -r requirements.txt
```

### 2. Set Your API Key
You'll need a Google Gemini API key to power the extraction:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. Run a Specific Strategy
By default, the script uses the `native_multimodal` approach:
```bash
python main.py "../25221 - 61 Sefton Rd - Combined Structurals - 12Aug25 (6).pdf" "../00.1 - Energy Efficiency Report.pdf" --approach native_multimodal
```

### 4. Run & Evaluate All Strategies
Want to see how they all compare? You can run an automated evaluation against a ground truth dataset:
```bash
python run_all.py "../25221 - 61 Sefton Rd - Combined Structurals - 12Aug25 (6).pdf" --gt ground_truth.json
```
*This will execute every strategy, evaluate its accuracy, and generate a comprehensive `all_solutions_report.json` detailing outputs, latencies, and costs.*
