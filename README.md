# Construction PDF Analysis Service

[![Pytest CI](https://github.com/Amahseyn/TaskBuildern/actions/workflows/pytest.yml/badge.svg)](https://github.com/Amahseyn/TaskBuildern/actions/workflows/pytest.yml)

Welcome to the **Construction PDF Analysis Service**! This project is a robust, Python-based pipeline designed to extract structural and architectural estimation signals from complex, multi-source construction PDFs (like floor plans, engineering drawings, and energy efficiency reports). 

Construction documents are notoriously ambiguous and inconsistent. Rather than relying on brittle OCR logic and hardcoded rules, this tool leverages advanced large language models (specifically the Gemini 1.5/2.5 series) to reason through these documents and output a clean, schema-validated JSON payload ready for estimation.

---

## Architecture & Strategy

To find the perfect balance between cost, accuracy, and processing speed, this service implements a **multi-architecture Strategy Pattern** with 7 unique extraction approaches. 

Here is how each method performs based on our evaluation metrics:

| Approach | Accuracy | Cost | Latency |
| :--- | :--- | :--- | :--- |
| **1. Native Multimodal** (File API) | **High (90-95%)**. Reads text and spatial visuals. | **Medium ($$)**. Billed per page image + tokens. | **Slow (15-60s)**. API processing delays. |
| **2. Pure Text** | **Low-Medium**. Fails on unselectable raster drawings. | **Low ($)**. Input text tokens only. | **Fast (2-5s)**. Local text extraction. |
| **3. Hybrid Chunking** | **Medium**. Drops critical pages occasionally. | **Very Low (< $)**. Minimal text tokens used. | **Very Fast (1-3s)**. Tiny text prompt size. |
| **4. OCR Pipeline** | **Medium**. Catches raster text, loses structural context. | **Low ($)**. Compute cost shifted locally. | **Very Slow (2-4m)**. Local OCR bottleneck. |
| **5. Vision VLM** (Payload) | **High (90-95%)**. Exact same reasoning as Native. | **High ($$$)**. Raw image byte payload over wire. | **Slow (20-40s)**. Massive payload transfer. |
| **6. Two-Stage Hybrid** | **Medium-High (85-90%)**. Intelligent escalation. | **Low-Medium ($)**. Cheap most of the time. | **Medium (5-20s)**. Fast mostly, slow on vision. |
| **7. Chain-of-Thought** | **Very High (95%+)**. Advanced self-correction logic. | **High ($$$)**. Double inference costs. | **Very Slow (30-90s)**. Two sequential LLM calls. |

*Note: Our core prompts heavily emphasize avoiding hallucinations. Every extracted field includes strict `"confidence"` scores and `"reasoning"`, and any unanswerable ambiguities are cleanly aggregated into an `"openQuestions"` array.*

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

1. **Vector DB / RAG Integration**: For massive 500+ page projects, we'll add a visual embedding model (like ColPali) to retrieve only the most relevant sheets before passing them to the LLM.
2. **Deterministic Pre-processing**: A lightweight classification microservice to automatically tag pages (e.g., "Elevation", "Floor Plan") before routing them.
3. **Interactive Frontend**: A sleek web UI for estimators to drag-and-drop PDFs, review the JSON output, and provide corrections to continuously fine-tune the prompts.
4. **Ensemble Verification**: A rules-based algorithm layer (like regex cross-checking) to independently verify the LLM’s extracted metrics.

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
