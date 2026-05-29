# Construction PDF Analysis Service

[![Pytest CI](https://github.com/Amahseyn/TaskBuildern/actions/workflows/pytest.yml/badge.svg)](https://github.com/Amahseyn/TaskBuildern/actions/workflows/pytest.yml)

Welcome to the **Construction PDF Analysis Service**! This project is a robust, Python-based pipeline designed to extract structural and architectural estimation signals from complex, multi-source construction PDFs (like floor plans, engineering drawings, and energy efficiency reports). 

Construction documents are notoriously ambiguous and inconsistent. Rather than relying on brittle OCR logic and hardcoded rules, this tool leverages advanced large language models (specifically the Gemini 1.5/2.5 series) to reason through these documents and output a clean, schema-validated JSON payload ready for estimation.

---

## Architecture & Strategy

To find the perfect balance between cost, accuracy, and processing speed, this service implements a **multi-architecture Strategy Pattern** with 7 unique extraction approaches. It dynamically leverages the right tool for the job:
- **PyMuPDF (`fitz`)**: For lightning-fast programmatic text and metadata extraction from digital-native PDFs.
- **Tesseract OCR**: As a fallback for scanned documents or rasterized images where native text is missing.
- **Vision/Language Models (Gemini)**: For spatial reasoning, unstructured data mapping, and resolving domain-specific construction terminology.

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

### Confidence Scoring & Reducing Hallucinations

To guarantee enterprise-grade reliability and minimize hallucinations, the system employs several strict guardrails:
1. **Pydantic Schema Validation**: Forces the LLM to return data in a predictable, typed JSON structure. If the model hallucinates a field type, it is caught immediately.
2. **Mandatory Reasoning**: The model is forced to output a `"reasoning"` string for *every* extracted structural component, effectively creating a Chain-of-Thought process that reduces hallucinated leaps in logic.
3. **Explicit Confidence Scores**: Every piece of data comes with a `"confidence"` rating (0.0 to 1.0). Downstream systems can automatically flag low-confidence extractions for human review.
4. **"I Don't Know" Directives**: The prompt explicitly commands the model to return `null` or add to the `openQuestions` array rather than guessing missing information.

### Scaling to Thousands of Documents per Day

To scale this architecture to process thousands of PDFs daily, we would transition from a synchronous script to an event-driven microservices architecture:
1. **Asynchronous Message Queues**: Utilize RabbitMQ or AWS SQS to queue incoming PDFs, decoupling ingestion from the heavy extraction process.
2. **Parallel Processing**: Deploy the extraction workers across a Kubernetes cluster. 
3. **Smart Routing**: Use a lightweight heuristic router (e.g., assessing file size, scan type) to send easy text-native PDFs to cheaper/faster pure-text pipelines, saving expensive Vision LLM calls only for complex structural diagrams.
4. **API Load Balancing**: Distribute requests across multiple API keys/endpoints to avoid rate limits, while employing `Tenacity` for exponential backoff retries.

### Evaluating Quality

Quality is evaluated programmatically using our `run_all.py` suite. This tool runs all 7 extraction strategies against a benchmarked set of construction documents and a verified `ground_truth.json`. It automatically calculates:
- **Accuracy**: By comparing the extracted JSON fields against the ground truth schemas.
- **Latency**: Measuring end-to-end execution time.
- **Cost**: Estimating token usage based on the specific strategy used.
This allows us to continuously monitor system regressions whenever prompts or models are updated.

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
9. **YOLO & Computer Vision Integration**: Implement YOLO and combine it with other CV or PDF extraction tools for structured data extraction to significantly improve latency.
10. **LLM Fine-tuning**: Fine-tune LLMs specifically on construction documents to increase extraction accuracy.
11. **Model Testing & Evaluation**: Test various LLM models locally (e.g., via Ollama) or through different APIs to continually assess and improve overall system performance.
12. **Performance Feedback Dashboard**: Create a comprehensive dashboard for users to easily provide feedback on extraction performance, enabling a continuous improvement loop.
13. **Dynamic LLM Fallback Orchestration**: Implement an intelligent fallback router to seamlessly switch between local, privacy-first models (e.g., via Ollama) and powerful cloud APIs (e.g., Gemini) based on document complexity, latency requirements, and API availability.
14. **MLflow Integration**: Integrate MLflow (or similar tools like LangSmith) for comprehensive experiment tracking, logging prompt versions, tracing LLM outputs, and monitoring extraction accuracy over time.

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
