# SchemeShift — Release checklist

Updated: 17 November 2026

## Engineering checks

- [x] Backend tests (31 passing).
- [x] Python compilation.
- [x] Synthetic searchable-PDF upload through pypdf, mocked extraction, quote verification, diff, and profile evaluation.
- [x] Same-origin `/api` configuration and Vite proxy.
- [x] Docker Compose/Nginx deployment configuration authored.
- [ ] Run `npm install` and `npm run build` on a network-enabled machine.
- [ ] Run `docker compose up --build` and check `/api/health` plus browser upload flow.
- [ ] Configure a Gemini API key locally and run a real extraction. Never share the key in chat or commit it.
- [ ] Run a complete live Gemini + real-PDF upload and manually score every extracted rule against page text.
- [ ] Perform final browser tests at desktop and mobile widths.

## Research and evaluation checks

- [ ] Retrieve the original G.O.(Rt) No.11/2014/BCDD PDF; resolve the 24 Jan vs 29 Jan date discrepancy from the original.
- [ ] Retrieve and classify G.O.(Rt) No.69/2014/BCDD.
- [ ] Retrieve G.O.(Ms) No.03/2018/BCDD and verify whether it actually modifies the overseas scholarship rules.
- [ ] Retrieve G.O.(Rt) No.39/2021/BCDD; distinguish it from beneficiary-selection orders.
- [ ] Retrieve and manually compare G.O.(Ms) No.387/2025/HEDN and G.O.(Ms) No.603/2025/HEDN; resolve the date discrepancy for 387 from the PDF.
- [ ] Only promote a scholarship pair into `gold_pairs/` after both source documents and a human-checked answer key are present.

## Release and presentation

- [ ] Test a clean install using README instructions.
- [ ] Verify no `.env`, API key, applicant personal data, or local upload has entered the archive/repository.
- [ ] Record a short demo using public documents only and label any snapshot comparison accurately.
- [ ] Keep the disclaimer visible: SchemeShift is an independent research prototype, not an official government eligibility decision.

## Do not claim

- No verified full scholarship amendment chain yet.
- No live Gemini extraction accuracy benchmark yet.
- No official scholarship PDF extraction test yet.
- No production build or Docker runtime verification yet.
- No general Malayalam legal-language understanding.
