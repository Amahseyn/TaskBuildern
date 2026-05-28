# Construction PDF Analysis Service

This project provides a Python service to extract structural and architectural estimation signals from multiple construction PDFs (e.g., drawings, energy efficiency reports). It reads inconsistent, ambiguous, and multi-source inputs and produces a clean, schema-validated JSON payload for estimation.

## Your Approach

Construction documents are often multi-source, inconsistent, and highly complex. Rather than relying on brittle OCR logic paired with hardcoded NLP rules, this solution implements a **multi-architecture strategy pattern** centered around large language models (Gemini 1.5/2.5 series).

I implemented **7 different approaches** to evaluate the trade-offs between cost, accuracy, and latency, ranging from pure text extraction to complex multimodal reasoning:

1. **v1: Native Multimodal (Gemini File API)** - Uploads raw PDFs. Highly accurate, relies on the LLM's spatial reasoning. (Primary Approach)
2. **v2: Pure Text Extraction (PyMuPDF)** - Strictly extracts text, drops visuals. Fast and cheap, but fails on rasterized drawings.
3. **v3: Hybrid Chunking** - Uses keyword density scoring to only pass relevant pages (e.g., schedules, schedules, structural drawings) to the LLM, reducing token cost.
4. **v4: OCR Pipeline (pdf2image + Tesseract)** - Rasterizes pages and runs traditional OCR locally. Very slow but works for scanned PDFs.
5. **v5: Vision VLM (Base64/Image Payload)** - Sends converted image frames over the wire. Very accurate but has massive payload overhead.
6. **v6: Two-Stage Hybrid (Text + Vision Escalation)** - Uses v3 for cheap extraction, then escalates to v5 *only* for missing or low-confidence fields.
7. **v7: Chain-of-Thought Self-Verification** - A two-pass system where the LLM reviews its own output for consistency across different documents.

The core extraction prompt heavily emphasizes avoiding hallucinations, enforcing the use of `"confidence"` and `"reasoning"` strings for every key field, and aggregating unanswerable ambiguities into an `"openQuestions"` array.

## Tools/Libraries Used

- **Python 3**
- **google-generativeai**: For interacting with the Gemini 2.5 Flash/Pro multimodal capabilities.
- **pydantic**: Crucial for strictly enforcing the expected schema (`ExtractionResult`) and defining complex nested objects. This enforces structured JSON output.
- **tenacity**: For robust retry logic, handling rate limits and transient API failures gracefully.
- **PyMuPDF (`fitz`)**: For extremely fast local text extraction and structural analysis of PDF pages (used in text-based approaches).
- **pdf2image** & **pytesseract**: For rasterization and local OCR fallback.

## Limitations

- **Latency**: Processing time using the native multimodal API (v1) or vision payloads (v5/v6) can take 15-60 seconds, which is slow for synchronous real-time web requests.
- **Complex Tables**: While multimodal models are excellent at spatial reasoning, they can still occasionally misread highly dense, microscopic grid numbers on sprawling A0 engineering drawings.
- **Cost**: Processing 100-page structural document sets entirely via Vision/Multimodal LLMs can quickly accrue token costs if not strategically chunked or escalated (as attempted in v3/v6).

## What You Would Improve With More Time

1. **Vector DB / RAG Implementation**: For massive, 500+ page project sets, I would implement a Retrieval-Augmented Generation pipeline using a visual embedding model (like ColPali) to retrieve only the 5-10 relevant sheets before asking the LLM to extract data.
2. **Deterministic Pre-processing Pipeline**: Build a microservice that automatically classifies pages (e.g., "Elevation", "Section", "Floor Plan", "Report") using lightweight models before routing them to the expensive LLM.
3. **Frontend Integration**: Develop a simple web UI (e.g., using Streamlit or Next.js) allowing estimators to drag-and-drop PDFs and iteratively correct the JSON output, effectively creating a feedback loop to further fine-tune the prompts.
4. **Detailed Confidence Scoring Matrix**: Integrate an ensemble approach where traditional rule-based algorithms cross-verify the LLM's output (e.g., running regex against the OCR text to cross-check the LLM's room count).

---

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set API Key:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```
3. Run a specific strategy (default is native_multimodal):
   ```bash
   python main.py "arch_drawings.pdf" "struct_plans.pdf" "energy_report.pdf" --approach native_multimodal
   ```

4. Run and evaluate ALL strategies at once:
   ```bash
   python run_all.py "arch_drawings.pdf" "struct_plans.pdf" "energy_report.pdf" --gt ground_truth.json
   ```
   This will execute every strategy, evaluate its accuracy against the ground truth, and dump a comprehensive JSON report containing all outputs, latencies, and costs into `all_solutions_report.json`.
