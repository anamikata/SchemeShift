# SchemeShift

**Kerala Government Order Change & Eligibility Impact Analyzer**

SchemeShift compares two supplied versions of a government order or scheme guideline. It uses AI to extract explicit conditions with source quotations, verifies that quotations against the uploaded PDF text, compares only verified rules, and optionally evaluates a sample applicant profile against the conditions found in each uploaded document.

> This is an independent research prototype, not a government service or an official eligibility decision. A condition absent from an amendment is not automatically considered repealed. Parent orders and referenced documents may contain continuing requirements.

## Current MVP scope

- Upload two searchable PDF documents.
- Extract PDF text page by page in memory.
- Use Gemini structured output to extract a normalized rule list and document metadata.
- Verify each extracted quotation against the stated source page and check that the extracted value, unit, and numeric operator are supported by the quotation.
- Normalize Indian comma-grouped amounts and Malayalam numerals for evidence checks; support a conservative set of Malayalam operator/unit phrases.
- Compare verified rules as modified, unchanged, not restated in the newer document, or not found in the older document. Conditional or ambiguous rules are escalated for review.
- Include the uploaded filenames, page counts, and SHA-256 hashes in the report for reproducibility.
- Optionally evaluate a sample applicant profile using deterministic code. Applicant profile fields are not sent to Gemini. If a condition is missing from one supplied version, that side is marked insufficient rather than silently assuming repeal or introduction.
- English and Malayalam UI labels, comparison explanations, and model-requested rule explanations where available.

### Known limitations

- Scanned PDFs are rejected with a clear message; OCR is not implemented yet.
- Only a deliberately limited set of rule types can be evaluated automatically. Other fields are displayed for human review.
- Malayalam phrase support is a small tested lexicon, not general-purpose Malayalam legal-language validation. Unrecognized wording should be marked for human review.
- Only explicit, quote-verified limited-scope statements are used to carry forward omitted conditions. Other incomplete amendment chains remain unknown. The MVP does not automatically consolidate a complete amendment chain.
- Profile outcomes cover only verified, explicit, supported conditions found in the relevant uploaded document. They are not an overall legal eligibility determination.
- Gemini extraction is not guaranteed correct merely because a quotation is present. The quote check establishes textual provenance, not the legal correctness of the model's interpretation. Human-labelled evaluation is required.

## Project structure

```text
SchemeShift/
  backend/
    app/
      ai_extract.py
      compare.py
      evaluate.py
      evidence.py
      main.py
      models.py
      pdf_extract.py
      settings.py
    tests/
    requirements.txt
    .env.example
  frontend/
    src/
    package.json
    vite.config.js
  research/
    source-audit-2026-11-15.md
    source_registry.json
    gold_pairs/pwd_erratum_2025.json
```

## Run locally on Windows

### 1. Backend

Open PowerShell in the `backend` folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and add your Gemini API key locally:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash
GEMINI_FALLBACK_MODEL=gemini-3.5-flash-lite
MAX_UPLOAD_MB=18
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Do not commit or share the `.env` file. Never paste an API key into a public repository or screenshot.

On HTTP 503 capacity failures, SchemeShift makes up to three bounded attempts per model and then tries the configured fallback. The fallback defaults to `gemini-3.5-flash-lite`; set `GEMINI_FALLBACK_MODEL=` to disable it. Temporary HTTP 429 rate limits are retried without switching models; responses that indicate exhausted quota stop immediately. Both models use the same JSON schema and existing evidence-verification pipeline.

Start the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

API health check: http://localhost:8000/api/health
Interactive API docs: http://localhost:8000/docs

### 2. Frontend

Open a second terminal in the `frontend` folder:

```powershell
npm install
npm run dev
```

Open the local URL printed by Vite (normally http://localhost:5173).

If the backend is hosted at a different URL, create `frontend/.env` with:

```env
VITE_API_BASE=https://your-backend.example
```

Restart Vite after changing environment variables.

## Run with Docker Compose (single-origin setup)

Docker Compose builds the React frontend and FastAPI backend, serves the frontend on port 8080, and proxies `/api` requests internally to the backend. This avoids hard-coding a backend URL into the browser bundle.

1. Install Docker Desktop (or Docker Engine with Compose).
2. Copy `.env.example` to `.env` in the project root.
3. Add your Gemini key to the root `.env` file. Do not commit it.
4. From the project root, run:

```powershell
docker compose up --build
```

Open http://localhost:8080. Check http://localhost:8080/api/health. Stop with `Ctrl+C`, or run `docker compose down`. The backend is not published as a separate host port; only the frontend gateway is exposed. Configure HTTPS, access controls, request rate limits, and hosting secrets before any public deployment.

For local development, the Vite dev server proxies `/api` to `http://127.0.0.1:8000` by default. Set `VITE_BACKEND_TARGET` if the backend runs elsewhere.

## Run tests

From the `backend` folder:

```powershell
python -m pytest -q
```

The 31 backend tests cover quotation/value/unit/operator verification, Indian comma-grouped amounts, Malayalam numerals and selected Malayalam phrases, safe treatment of missing and conditional amendment clauses, duplicate-rule review, deterministic profile checks, safe handling of amendment uncertainty, early upload-size rejection, a mocked end-to-end API request, an official PWD erratum regression fixture that tests parent-order linking, limited-scope carry-forward, and unit-sensitive diffs, and a synthetic PDF multipart-ingestion test that exercises real pypdf extraction with Gemini mocked. They do not test live Gemini extraction or official scholarship-PDF accuracy.

Frontend source syntax was checked with the installed TypeScript JSX parser. A production Vite build has **not** yet been run because dependency installation timed out in this environment; run `npm install` and `npm run build` on a network-enabled development machine before treating the frontend as build-verified.

## Research status

See [`research/source-audit-2026-11-15.md`](research/source-audit-2026-11-15.md). The audit is preliminary. A candidate source pair must not be treated as a validated evaluation example until both documents are located, the relevant clauses are manually compared, and a human-labelled answer key is recorded.

## Privacy and responsible use

- Uploaded PDFs are held in memory for request processing and are not persisted by this MVP.
- Extracted document text is sent to the configured Gemini API for rule extraction. Use public documents only in the prototype. Google's current terms say unpaid Gemini API / AI Studio content may be used to improve Google products and may be reviewed by humans; do not submit confidential or personal data. The applicant profile is not sent to Gemini.
- Applicant profile fields are evaluated by backend code and are not included in the Gemini prompt.
- Do not enter real sensitive personal data into the demo.
- Do not present the report as official government advice, approval, or an eligibility decision.

## Current build checkpoint (16 November 2026)

- Backend test suite: **31 passed**.
- Frontend JSX syntax: checked; production dependency install/build: pending.
- Live Gemini extraction: pending a locally configured API key and test against real source PDFs.
- Research corpus: preliminary leads recorded; no scholarship pair is yet certified as a human-labelled gold pair. The OBC 2024/2026 documents support a policy-snapshot comparison only; the 2014 parent order remains outstanding.
- The PWD 2025 erratum pair is now a manually annotated regression fixture for numeric/unit changes and explicit limited-scope amendments. It is not a scholarship eligibility example and must not be presented as one.


## Research checkpoint — 16 November 2026

Latest local verification on 16 November: 31 backend tests passed, Python compilation passed, and research JSON validation passed. The OBC scholarship comparison remains a policy-snapshot candidate, not a verified direct amendment pair. See STATUS.md and NEXT_STEPS.md for limitations and research gates.


## Synthetic PDF ingestion test

The files in `backend/tests/fixtures/` are deliberately labelled synthetic and are not Government Orders. They allow automated tests to exercise actual PDF byte uploads, local pypdf text extraction, quote verification, rule comparison, and local profile evaluation while mocking Gemini. They must never be presented as source evidence or as proof of live Gemini accuracy.


### Research update — 16 November 2026

The OBC source audit now records an unresolved parent-order date discrepancy: the 2026 revised GO cites G.O.(Rt) No.11/2014/BCDD as dated 24 January 2014, while two official BCDD application forms print 29 January 2014. The forms are not substitutes for the original GO. G.O.(Ms) No.03/2018/BCDD is listed in the official BCDD handbook and in the 2019 overseas-scholarship case exhibit list, but it is described as a creamy-layer income-limit order; it is not treated as a verified scholarship amendment. See `research/source-audit-2026-11-15.md` and `research/source_registry.json`.


## Engineering checkpoint — 17 November 2026

- Backend: 31 tests pass; Python compilation passes.
- Gemini model default: `gemini-3.8-flash` (confirm current access for your API key in Google AI Studio).
- Frontend: same-origin `/api` requests; Vite development proxy and Nginx production reverse proxy added.
- Docker Compose deployment files added; Docker image build has not been run in this workspace.
- Production Vite build remains unverified because `npm install` timed out here.
- Real official scholarship-PDF extraction and live Gemini accuracy remain unverified. The official PDFs must be downloaded and checked locally before any scholarship comparison is called validated.
- Current research audit and unresolved source references remain in `research/`.

### Explicit amendment-pair verification

For errata and amendment orders that explicitly state a before-and-after correction, SchemeShift can now display a dedicated amendment-pair panel. A pair is marked verified only when the exact correction quotation is present on the cited page of the newer PDF, both original and corrected values/units are supported by that quotation, the original amount/unit is found in the uploaded older PDF, and the parent-order plus limited-amendment scope checks pass. These pairs are displayed separately from general rule differences. Missing or unverified pairs are not treated as confirmed changes.
