# SchemeShift — Working checkpoint

**Updated:** 17 November 2026

## Implemented

- Bilingual React/Vite UI (English/Malayalam) for two searchable-PDF uploads, optional applicant profile, evidence display, rule diff, and warnings.
- FastAPI API with in-memory PDF processing, Gemini structured extraction, page-level quote/value/operator/unit verification, conservative rule comparison, and deterministic limited-field applicant evaluation.
- Conservative handling of missing clauses and limited-scope amendments; no automatic assumption that omitted rules are repealed.
- SHA-256 document fingerprints and source-page references.
- Synthetic end-to-end PDF upload regression test with real pypdf extraction and mocked Gemini.
- Explicit PG/Postgraduate and PhD/doctoral aliases; no fuzzy matching.
- Same-origin frontend API requests, Vite development proxy, Nginx production reverse proxy, Dockerfiles, Docker Compose, and health checks.

## Verification completed

- `python -m pytest -q`: **31 passed**.
- `python -m compileall -q app tests`: passed.
- Research registry JSON: valid in the previous v8 verification; revalidate before release.
- ZIP integrity: v8 verified; next release archive must be checked after packaging.

## Not yet verified / external blockers

- `npm install` timed out in this workspace; production Vite build has not been verified.
- Docker is not available/has not been run here; Docker image build and compose startup are unverified.
- Direct downloads of official Kerala PDF hosts failed DNS resolution from this workspace.
- Live Gemini calls require the user's own API key and quota; not tested.
- No complete, manually labelled scholarship amendment pair is currently certified.

## Research safety

- OBC 2024 and 2026 orders are a policy-snapshot candidate, not a verified direct parent/amendment pair. Historical rank ceiling and batch-specific selection cutoff must remain distinct.
- G.O.(Rt) No.11/2014/BCDD parent order remains outstanding; date conflict 24 Jan (cited by later GOs) vs 29 Jan (shown on BCDD application forms) remains unresolved.
- G.O.(Rt) No.69/2014/BCDD and G.O.(Ms) No.03/2018/BCDD operative text/relationship remain unverified.
- G.O.(Rt) No.39/2021/BCDD is an identified reference cited in G.O.(Rt) No.08/2022/BCDD; its official PDF remains outstanding.
- CM Researcher G.O.(Ms) No.387/2025/HEDN and No.603/2025/HEDN full PDFs and clause-by-clause comparison remain outstanding. The 13 June vs 16 June 2025 date discrepancy for G.O.387 is unresolved.
- The PWD 2025 erratum is an engineering regression fixture only, not a scholarship gold pair.

## Run locally

See `README.md`. For local dev, run the backend on port 8000 and `npm run dev` in `frontend`; Vite proxies `/api`. For the single-origin Docker setup, copy `.env.example` to `.env`, set `GEMINI_API_KEY`, and run `docker compose up --build`.

## Amendment-pair improvement (2026-11-22)

- Added a dedicated structured representation for explicit before/after amendment corrections.
- Gemini extraction now asks for numeric values and units separately and captures the exact correction quotation, target paragraph/clause, and page.
- Backend verification checks the amendment quote on the cited page, both values and units in that quote, the original amount/unit in the uploaded older PDF, and the already-verified parent-order/limited-scope link.
- The API returns verified/unverified amendment pairs separately from general rule diffs.
- Generic “not found in older document” rows are suppressed only when their exact quotation is already represented by a verified amendment pair; unrelated rows and uncertainty safeguards remain unchanged.
- Frontend displays a dedicated before → corrected panel with source excerpts from both documents.
- Frontend value formatting avoids repeating a unit already present in the extracted value.
- Backend test suite: 34 passed. Python compilation passed. Frontend production build was not run in this environment because frontend dependencies could not be installed before timeout; run `npm.cmd run build` on the Windows machine after replacing the project files.
