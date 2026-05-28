# 🏗️ Construction PDF Analysis Service

[![Pytest CI](https://github.com/Amahseyn/TaskBuildern/actions/workflows/pytest.yml/badge.svg)](https://github.com/Amahseyn/TaskBuildern/actions/workflows/pytest.yml)

Welcome to the **Construction PDF Analysis Service**! This project is a robust, Python-based pipeline designed to extract structural and architectural estimation signals from complex, multi-source construction PDFs (like floor plans, engineering drawings, and energy efficiency reports). 

Construction documents are notoriously ambiguous and inconsistent. Rather than relying on brittle OCR logic and hardcoded rules, this tool leverages advanced large language models (specifically the Gemini 1.5/2.5 series) to reason through these documents and output a clean, schema-validated JSON payload ready for estimation.

---

## 🚀 Architecture & Strategy

To find the perfect balance between cost, accuracy, and processing speed, this service implements a **multi-architecture Strategy Pattern** with 7 unique extraction approaches:

1. **Native Multimodal (Gemini File API)** 🌟 *(Primary Approach)* - Directly processes raw PDFs using spatial reasoning. Highly accurate and reliable.
2. **Pure Text Extraction (PyMuPDF)** - Strictly extracts text while dropping visuals. It’s lightning-fast and cost-effective, though it struggles with rasterized drawings.
3. **Hybrid Chunking** - Uses keyword density scoring to filter and send only relevant pages (e.g., schedules, structural plans) to the LLM, significantly reducing token costs.
4. **OCR Pipeline (pdf2image + Tesseract)** - Rasterizes pages and runs traditional local OCR. Perfect as a fallback for scanned, non-searchable PDFs.
5. **Vision VLM (Base64/Image Payload)** - Sends converted image frames over the wire. Offers incredible accuracy at the expense of a larger payload overhead.
6. **Two-Stage Hybrid (Text + Vision Escalation)** - Starts with cheap text extraction (v3), then intelligently escalates to vision (v5) *only* for missing or low-confidence data fields.
7. **Chain-of-Thought Self-Verification** - A dual-pass system where the LLM reviews and critiques its own initial output to ensure cross-document consistency.

*Note: Our core prompts heavily emphasize avoiding hallucinations. Every extracted field includes strict `"confidence"` scores and `"reasoning"`, and any unanswerable ambiguities are cleanly aggregated into an `"openQuestions"` array.*

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **[google-generativeai](https://pypi.org/project/google-generativeai/)**: Powers the core multimodal reasoning capabilities.
- **[Pydantic](https://docs.pydantic.dev/)**: Enforces strict JSON schemas (`ExtractionResult`) for robust, predictable outputs.
- **[Tenacity](https://tenacity.readthedocs.io/)**: Provides resilient retry logic to gracefully handle rate limits and transient API hiccups.
- **[PyMuPDF (`fitz`)](https://pymupdf.readthedocs.io/)**: Delivers blazing-fast local text extraction and structural PDF analysis.
- **pdf2image** & **pytesseract**: Local rasterization and OCR fallback.

---

## 🚦 Current Limitations

While powerful, the system has a few known constraints:
- **Latency**: Fully multimodal approaches can take 15-60 seconds, which might be too slow for synchronous, real-time web requests.
- **Complex Tables**: Despite excellent spatial reasoning, models can occasionally misread highly dense, microscopic grid numbers on sprawling engineering plans.
- **Cost**: Processing massive 100+ page document sets entirely via Vision LLMs can accrue token costs quickly if not using our optimized chunking or escalation strategies.

---

## 🔮 Future Roadmap

Here’s what we are planning to build next:

1. **Vector DB / RAG Integration**: For massive 500+ page projects, we'll add a visual embedding model (like ColPali) to retrieve only the most relevant sheets before passing them to the LLM.
2. **Deterministic Pre-processing**: A lightweight classification microservice to automatically tag pages (e.g., "Elevation", "Floor Plan") before routing them.
3. **Interactive Frontend**: A sleek web UI for estimators to drag-and-drop PDFs, review the JSON output, and provide corrections to continuously fine-tune the prompts.
4. **Ensemble Verification**: A rules-based algorithm layer (like regex cross-checking) to independently verify the LLM’s extracted metrics.

---

## 💻 Usage & Installation

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
