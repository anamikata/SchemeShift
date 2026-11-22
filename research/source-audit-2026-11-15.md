# SchemeShift — Initial Source Audit

**Audit date:** 15 November 2026  
**Scope:** Kerala government orders and public scheme documents  
**Status:** Preliminary source discovery. This is not yet a fully validated gold dataset.

## Executive finding

There are credible official source trails for versioned government rules in Kerala. Two promising scholarship examples have been identified, plus several official amendment/erratum orders that can test numerical and clause-level change detection. The exact old/new PDFs and full amendment chains still need to be collected and manually checked before we treat any pair as a benchmark.

The initial MVP should support **user-supplied PDFs and a small curated set of reviewed examples**. Do not hardcode an assumption that every cited order is available or that an amendment replaces the full parent order.

## Candidate pair A — Overseas Scholarship for OBC students

**New/revised order found:** G.O.(Rt) No. 6/2026/BCDD, dated 19 January 2026.  
**Official PDF:** https://document.kerala.gov.in/documents/governmentorders/govtorder2001202616%3A43%3A12.pdf

The 2026 order explicitly cites G.O.(Rt) No. 11/2014/BCDD dated 24 January 2014, describes proposed modifications to existing scheme guidelines, issues revised administrative sanction, and states that previous orders inconsistent with the new order stand dispensed with.

Fields visible in the 2026 order include eligible communities, university ranking, eligible disciplines, study level, scholarship tiers/amounts, minimum marks, age limit, annual family income, one-child-per-family restriction, and one-time-only restriction.

**Historical context found:** A 20 February 2024 BCDD order (G.O.(Rt) No. 10/2024/BCDD) describes the overseas OBC scholarship as supporting PG/PhD study abroad, notes the earlier top-200 Times Higher Education ranking condition and subsequent expansion to top 600, and mentions a family-income ceiling of ₹6 lakh. This is a beneficiary-selection order, not a substitute for the complete 2014 policy order.

**2026 order visible details:** OBC applicants; OEC preference within prescribed limits; minority-community students excluded; universities in the top 300 Times Higher Education ranking; PG or PhD abroad in listed disciplines; 60% minimum marks; below 40 years; annual family income up to ₹6 lakh; only one child per family; scholarship only once. Assistance is divided into three tiers.

**Status:** Strong candidate; exact 2014 source PDF still needs retrieval and full clause-by-clause comparison. Do not yet assert exactly which old eligibility clauses were removed or retained.

## Candidate pair B — CM Researcher Scholarship

**Original guideline order listed:** G.O.(Ms) No. 387/2025/HEDN, dated 13 June 2025.  
**Amending order listed:** G.O.(Ms) No. 603/2025/HEDN, dated 13 August 2025.  

Official Higher Education Department indexes:
- https://www.highereducation.kerala.gov.in/index.php/g-o-s-circulars/g-o-index-for-2025/ms-series-2025
- https://www.highereducation.kerala.gov.in/index.php/103-hedn/government-order/g-o-index-for-2025

The Directorate of Collegiate Education's 13 August 2025 notice gives operational guidelines for the CM Researcher Scholarship:
- ₹10,000 monthly fellowship;
- regular/full-time PhD research students;
- no other fellowship from Central/State Government, university or another funding agency;
- restricted to specified Kerala universities;
- up to three years of fellowship, subject to conditions;
- progress reports and other supporting documentation.

Official notice PDF: https://collegiateedu.kerala.gov.in/wp-content/uploads/2025/08/CM-RESEARCHER.pdf

**Status:** Promising pair because the official index explicitly identifies an original guideline order and a later amending order. The exact full text of both G.Os. and the precise clauses changed must still be retrieved. The August notice's extracted Malayalam text contains OCR/encoding noise; visual verification will be needed before it is used as gold data.

## Candidate pair C — LSGD committee modification (non-scholarship policy example)

**Modification order:** G.O.(Rt) No. 225/2022/LSGD, dated 4 February 2022.  
**Official PDF:** https://lsgd.kerala.gov.in/orders_and_circulars/oa-100-2021-state-level-committee-and-district-level-committee-modifications-orders-issued-_x000d_/

The order says it modifies committee composition by adding representatives to State and District Level Committees, and that the prior order is modified only to that extent. It cites G.O.(Rt) No. 2485/2021/LSGD in its 'Read' section; its body also refers to an earlier committee-formation order. This chain needs reconciliation before the documents are paired in the app.

**Status:** Useful for testing clause-level amendment language and linked-order display; not a scholarship-eligibility demonstration.

## Candidate pair D — PWD numerical erratum (numeric-diff test)

**Erratum:** G.O.(Rt) No. 1247/2025/PWD, dated 14 August 2025.  
**Official PDF:** https://document.kerala.gov.in/documents/governmentorders/govtorder2108202511%3A25%3A32.pdf

The erratum corrects figures in G.O.(Rt) No. 1217/2025/PWD: values mistakenly expressed as ₹350 crore and ₹689 crore are corrected to ₹350 lakh and ₹689 lakh.

**Status:** Excellent narrow test case for numerical change extraction, unit normalization and quote verification. It is not an applicant-eligibility case and should not be used to imply a scheme-profile decision.

## Additional source leads

- Kerala Government Document Portal: https://document.kerala.gov.in/ — department-level order search and official document records.
- Higher Education Department G.O. indexes contain explicit entries for revised/modified guidelines.
- Kerala LSGD and PWD websites publish amendment/erratum orders that can test the rule-diff engine.
- The Compassionate Employment Scheme portal (https://ces.kerala.gov.in/) publishes official explanations of G.O.(P) No. 4/2025/P&ARD and later amendments. This is a possible future rules-impact example but is legally sensitive and should be excluded from the initial scholarship demo unless independently checked.

## Data handling and product rules

1. Store source URL, publisher/department, order number, order date, document version, access date, and a content hash.
2. Keep page-level text and the original PDF. The extracted quote shown to a user must be traceable to a page.
3. Do not put beneficiary lists or applicant personal data into the demo corpus. One found 2024 scholarship selection order contains names and addresses; it is not suitable as a public demo asset.
4. A cited old order is not proof that its full text is present. Show “referenced order not in corpus” when missing.
5. A clause absent from an amendment is not automatically “removed”. Use “not restated / not found in this document” unless the text explicitly repeals or replaces it.
6. Separate explicit, conditional, ambiguous and unobserved rules.
7. The applicant profile evaluator must return “insufficient evidence” whenever a required condition or parent order is unavailable.
8. Keep source facts and AI interpretations separate. AI-extracted values require verbatim quote verification and human review before inclusion in the gold dataset.

## Next research gates

- Retrieve the full 2014 Overseas Scholarship G.O. and compare its complete conditions with the 2026 revised order.
- Retrieve G.O.(Ms) 387/2025/HEDN and G.O.(Ms) 603/2025/HEDN; compare their exact clauses and the August implementation notice.
- Collect at least three complete and manually verified pairs before expanding toward a 10-pair corpus target.
- Test text extraction on each source PDF; classify it as text PDF, mixed PDF, or scanned/low-quality PDF.
- Label fields and changes manually before running AI extraction. Do not use model output as its own ground truth.

## Research update — 15 November 2026 (second pass)

### CM Researcher order pair: index confirmation strengthened; primary PDF retrieval still pending

The current official Higher Education Department index explicitly identifies:
- G.O.(Ms) No. 387/2025/HEDN as the original guideline order for the CM Research Scholarship (index date shown as 13 June 2025).
- G.O.(Ms) No. 603/2025/HEDN as an order amending guidelines for the CM-Researcher Scholarship (index date 13 August 2025).

Official index search records:
- https://www.highereducation.kerala.gov.in/index.php/g-o-s-circulars/g-o-index-for-2025/ms-series-2025
- https://www.highereducation.kerala.gov.in/index.php/103-hedn/government-order/g-o-index-for-2025

A separate Mahatma Gandhi University Academic A6 order, No. 6595/AC A6/2025/MGU dated 18 July 2025, cites G.O.(Ms) No. 387/2025/HEDN but gives the cited government order date as 16 June 2025. This differs from the department index date of 13 June 2025. Preserve this discrepancy as unresolved; do not silently normalize the date. The MGU order appears to amend a procedural condition for continuation/extension after six months and is not itself the original government order.

Source: https://research.mgu.ac.in/wp-content/uploads/2025/07/6595-AC_A_6-2025-.-.-.pdf

The Directorate of Collegiate Education's August notice and university notices corroborate that the scholarship was operationalized with ₹10,000 per month and restrictions on simultaneous fellowships. These are implementation notices, not substitutes for the full government orders.

**Status remains: promising candidate, not yet a verified gold pair.** Full text of both G.O. PDFs must be retrieved and manually compared before using them as a benchmark.

### Build readiness snapshot

A local prototype skeleton has been created:
- FastAPI backend with in-memory PDF text extraction (searchable/text PDFs only; scanned PDFs are rejected clearly).
- Gemini structured extraction schema for explicit rules and page quotations.
- Quote, value, unit and conservative numeric-operator checks.
- Rule diff that labels missing clauses as not restated/not found rather than repealed/new.
- Duplicate same-field rules are escalated for manual review.
- Deterministic profile checks for selected numeric and categorical conditions.
- React/Vite interface with English/Malayalam labels.

Historical checkpoint at the time of this note: 8 backend unit/API tests passed; the current suite count is recorded in STATUS.md and README.md. Live Gemini extraction has not been tested because no user API key has been configured. Frontend production build has not been run because npm dependency installation timed out in this environment; JSX syntax has been checked using the installed TypeScript parser. Do not claim a fully validated/deployed MVP yet.


## Research update — official pair evidence found in web verification

### PWD numerical erratum pair — both official PDFs located

This is a complete, high-confidence *numeric-diff* pair, but it is **not** an applicant eligibility example.

- Original: G.O.(Rt) No. 1217/2025/PWD, dated 11 August 2025. Official PDF: https://document.kerala.gov.in/documents/governmentorders/govtorder2108202511%3A20%3A25.pdf
- Erratum: G.O.(Rt) No. 1247/2025/PWD, dated 14 August 2025. Official PDF: https://document.kerala.gov.in/documents/governmentorders/govtorder2108202511%3A25%3A32.pdf
- The original order expresses two project amounts as Rs. 350 Crores and Rs. 689 Crores. The erratum corrects them to Rs. 350 Lakh and Rs. 689 Lakh, and explicitly says the original order is modified to that extent only.
- Use case: test number-plus-unit changes, page-level quotation verification, and careful distinction between corrected figures and unrelated eligibility conditions.
- Limitation: because the pair concerns a PWD work sanction rather than a welfare scheme, it should be used as an engineering test fixture, not as the main product demo.

Official source records were checked on 15 November 2026. The Government of Kerala document portal indexed both PDFs; the extracted erratum text explicitly gives the corrected figures and scope of modification.

### Overseas Scholarship for OBC students — revised order content independently checked

The official 19 January 2026 G.O.(Rt) No. 6/2026/BCDD PDF was opened and its text checked. It cites G.O.(Rt) No. 11/2014/BCDD, says it issues revised administrative sanction after proposed modifications, and contains eligibility conditions including top-300 Times Higher Education ranking, PG/PhD study, 60% marks, below-40 age, annual family income up to Rs. 6 lakh, one child per family, and one-time use.

Official PDF: https://document.kerala.gov.in/documents/governmentorders/govtorder2001202616%3A43%3A12.pdf

**Still not a validated old/new pair:** the complete 2014 G.O. has not yet been retrieved and checked against the 2026 order. Do not compare the 2024 beneficiary-selection order as though it were the full 2014 guideline.

### CM Researcher Scholarship index confirmation

The official Higher Education Department index lists G.O.(Ms) No. 387/2025/HEDN as the original CM Research Scholarship guideline order (13 June 2025), and the same department's index lists G.O.(Ms) No. 603/2025/HEDN as the later order amending the CM-Researcher Scholarship guidelines (13 August 2025).

Official indexes:
- https://www.highereducation.kerala.gov.in/index.php/g-o-s-circulars/g-o-index-for-2025/ms-series-2025
- https://www.highereducation.kerala.gov.in/index.php/103-hedn/government-order/g-o-index-for-2025

**Still pending:** retrieve both complete G.O. PDFs and manually compare the exact clauses. An index entry is not itself evidence of the exact changed rule.

## Research update — 15 November 2026 (additional official-source search)

### CM Researcher Scholarship: official indexes and implementation notice found

The Higher Education Department's official 2025 M.S. index lists G.O.(Ms) No. 387/2025/HEDN dated 13 June 2025 as the original CM Research Scholarship guideline order. Its official index for 2025 also lists G.O.(Ms) No. 603/2025/HEDN dated 13 August 2025 as an order amending the CM-Researcher Scholarship guidelines.

- Original-order index: https://www.highereducation.kerala.gov.in/index.php/g-o-s-circulars/g-o-index-for-2025/ms-series-2025
- Amendment-order index: https://www.highereducation.kerala.gov.in/index.php/103-hedn/government-order/g-o-index-for-2025
- Official Directorate of Collegiate Education implementation notice: https://collegiateedu.kerala.gov.in/wp-content/uploads/2025/08/CM-RESEARCHER.pdf

The implementation notice confirms that the programme was announced for full-time research scholars, with a ₹10,000 monthly fellowship, and that applicants receiving other fellowships such as JRF, MANF, RGNF or PMRF were excluded in that notice. It also lists 15 universities. This notice is useful corroborating material, but it is **not a substitute for the two Government Orders** and must not be used to infer the exact before/after clause changes.

**Status:** still a strong candidate, but the full 387/2025 and 603/2025 G.O. PDFs must be retrieved and their changed clauses manually compared before certifying this as a benchmark pair.

### Overseas Scholarship for OBC students: old order still missing

The official 19 January 2026 revised administrative-sanction order states that G.O.(Rt) No. 11/2014/BCDD dated 24 January 2014 issued the original administrative sanction and detailed guidelines, and that the 2026 order follows a proposal to modify those existing guidelines. The 2026 order's new conditions can be inspected, but the complete 2014 parent order was not found in this search.

A 2024 e-Grantz beneficiary-selection order and a 2015-era application form refer to the 2014 order, but neither is the complete 2014 guideline order. Do not treat either as a substitute old version.

Official 2026 revised order: https://document.kerala.gov.in/documents/governmentorders/govtorder2001202616%3A43%3A12.pdf

### Build safety update

- Gemini extraction instructions now explicitly treat PDF text as untrusted source data and ignore instructions embedded in uploaded documents.
- Each PDF is rejected after reading at most one byte beyond the configured upload cap, rather than loading the entire oversized file before checking its size.
- Diff quotations now carry old/new page references into the comparison report.
- A missing condition in one of the two uploaded documents now adds an explicit unknown to that side's profile assessment. Unless a known condition already fails, the status is downgraded to **insufficient evidence**. This prevents an amendment that omits an older condition from appearing to certify overall eligibility.
- Backend test suite is now 17 passing tests. This is still unit/mock verification; live Gemini extraction and evaluation on a manually labelled corpus remain pending.


## Research update — 15 November 2026 (amendment-scope benchmark)

### Official PWD original/erratum pair manually transcribed as an engineering fixture

- Original: G.O.(Rt) No.1217/2025/PWD, dated 11 August 2025.
- Erratum: G.O.(Rt) No.1247/2025/PWD, dated 14 August 2025.
- The erratum explicitly corrects Rs.350 Crores to Rs.350 Lakh and Rs.689 Crores to Rs.689 Lakh, then states that the parent order “stands modified to this extent only.”
- The original order also contains a separate final sanction amount of Rs.260 Lakhs. That amount is not repeated in the erratum; the explicit limited-scope sentence supports treating it as unchanged by this erratum, provided the parent-order link and scope quotation are verified.
- This is a strong test of number-plus-unit diffing and limited amendment scope. It is a PWD works sanction, **not** a scholarship eligibility example and not part of the user-facing scholarship gold corpus.

Sources:
- Original PDF: https://document.kerala.gov.in/documents/governmentorders/govtorder2108202511%3A20%3A25.pdf
- Erratum PDF: https://document.kerala.gov.in/documents/governmentorders/govtorder2108202511%3A25%3A32.pdf

The manually transcribed source excerpts, page references, expected changes, and interpretation note are stored in `research/gold_pairs/pwd_erratum_2025.json`. The regression test validates exact quote presence within the recorded page excerpts, the parent-order reference, the limited-scope quote, unit-aware changes, and carry-forward of the Rs.260 Lakhs clause. It does not replace a later local-PDF ingestion test.

### MGU University Junior Research Fellowship — related reference, not the same scheme

Mahatma Gandhi University Order No.6595/AC A6/2025/MGU, dated 18 July 2025, cites G.O.(Ms) No.387/2025/HEDN in its preamble as context. However, the operative order revises conditions for MGU's **University Junior Research Fellowship**, not the CM Researcher Scholarship. It should not be treated as an amendment or implementation order for CM Researcher Scholarship. It is excluded from the CM Researcher gold-pair corpus.

Source: https://research.mgu.ac.in/wp-content/uploads/2025/07/6595-AC_A_6-2025-.-.-.pdf

### Build update — explicit limited-scope amendment verification

The AI schema now requests amendment effect, cited parent order number/quote/page, and limited-scope quote/page. The backend does not trust that classification alone. It verifies: (1) the old order number appears in the uploaded older document, (2) the newer document's cited order number matches it, (3) the reference quote appears on the claimed page, (4) the scope quote appears on its claimed page, and (5) the scope quote contains a recognized explicit “to this extent only” phrase. Only then may an old rule absent from the erratum be labelled `unchanged_by_limited_amendment`. Otherwise it remains `not_restated_in_new_document` and eligibility is downgraded to insufficient evidence.

The comparison report now preserves old and new units, preventing a Crores-to-Lakh change from rendering visually as 350 → 350 with no visible distinction. Backend suite: 25 passing tests. Frontend JSX syntax checks pass; Vite production build remains unverified because dependency installation timed out in this environment.

## Additional OBC Overseas Scholarship policy snapshot (15 Nov 2026)

A further official source is now available for the Overseas Scholarship Scheme: G.O.(Rt) No.10/2024/BCDD dated 20 February 2024, hosted by eGrantz. Its opening policy section says the scheme serves OBC students pursuing PG/PhD study abroad with family income not exceeding ₹6 lakh; it records that the 2014 order initially covered Times Higher Education top-200 universities and that universities up to rank 600 were subsequently included. The same order separately records that the 2023-24 selection committee selected applicants from universities ranked up to 200. These are different concepts: the historical scheme eligibility ceiling and a particular year's selection cutoff. The order also says rankings should be checked and an order issued before applications are invited each financial year.

The official G.O.(Rt) No.6/2026/BCDD dated 19 January 2026 explicitly cites G.O.(Rt) No.11/2014/BCDD dated 24 January 2014 and issues revised administrative sanction. It limits eligibility to universities in the top 300 of the annual Times Higher Education World University Rankings; adds explicit Computer Science / Advanced Computer Technology / AI to the listed disciplines; limits study to foreign PG or PhD programmes; and states 60% minimum marks, age below 40, annual family income up to ₹6 lakh, one child per family, and one-time use.

**Research classification:** the 2024 and 2026 documents support a useful, source-backed policy-snapshot comparison, including a clearly visible ranking-ceiling difference (historical 600 ceiling vs 2026 top 300). However, the 2024 document is a beneficiary-selection order, not the complete original guidelines. It is therefore not a verified direct parent/amendment pair. The 2014 parent order and any intervening amendments are still required before labelling the comparison as a complete legal amendment chain or treating conditions absent from the 2024 snapshot as newly introduced in 2026.

Source URLs:
- 2024 official eGrantz PDF: https://egrantz.kerala.gov.in/egrantz_uploads/567b2892e6a16632626a78ced3de8bd3.pdf
- 2026 official Government Order PDF: https://document.kerala.gov.in/documents/governmentorders/govtorder2001202616%3A43%3A12.pdf

The 2024 order contains beneficiary names and addresses. Those personal details were intentionally not copied into the SchemeShift research fixture or dataset.


## Research update — 15 November 2026 (third pass)

### OBC Overseas Scholarship: primary text rechecked; comparison remains a candidate

The official 2024 selection order (G.O.(Rt) No.10/2024/BCDD, 20 February 2024) was opened and its PDF text inspected. Its opening policy-history section states that the original 2014 order covered Times Higher Education top-200 universities and that the scheme was later expanded to include universities up to rank 600 (PDF extracted lines 24–26). Separately, the 2023–24 selection decision chose applicants from universities ranked up to 200 (lines 34–36). These are different concepts: the scheme's historically expanded ceiling is not the same as that year's selection cutoff.

The official 2026 revised order, G.O.(Rt) No.6/2026/BCDD dated 19 January 2026, was also opened and inspected. It cites G.O.(Rt) No.11/2014/BCDD dated 24 January 2014 and says the Director proposed modifications to existing guidelines (PDF extracted lines 10–17). The revised text requires admission to a university in the annual THE top 300 (lines 22–25), lists eligible disciplines including Computer Science/AI and restricts study to foreign PG/PhD programmes (lines 26–28), and specifies 60% marks, below-40 age, ₹6 lakh annual family income, one child per family and one-time use (lines 48–53). It says previous orders inconsistent with this order stand dispensed with (line 84).

**Safe conclusion:** the 2024 text documents the historical top-600 expansion; the 2026 text states a top-300 rule. This supports a policy-snapshot comparison and an extraction test. It does **not** establish a complete direct clause-by-clause amendment diff because the cited 2014 guidelines and intervening orders are still absent. The 2024 PDF also contains personal beneficiary information; SchemeShift stores only policy clauses and excludes names/addresses.

Sources reviewed: https://egrantz.kerala.gov.in/egrantz_uploads/567b2892e6a16632626a78ced3de8bd3.pdf ; https://document.kerala.gov.in/documents/governmentorders/govtorder2001202616%3A43%3A12.pdf

### CM Researcher Scholarship: official evidence boundary

The Higher Education Department's official 2025 index identifies G.O.(Ms) No.387/2025/HEDN as the original CM Research Scholarship guidelines and G.O.(Ms) No.603/2025/HEDN as the subsequent amending order. The Directorate's 13 August 2025 PDF is an implementation/application notice and contains scheme conditions, but it is not a substitute for either Government Order. Until both full G.O. PDFs are retrieved, do not label the CM Researcher example as a verified gold amendment pair.

### Engineering check

A new regression test now guards against conflating the historical top-600 scheme ceiling with the 2023–24 batch-specific top-200 selection cutoff, and confirms that this candidate remains labelled as not a verified direct parent/amendment pair.


## Research update — 16 November 2026 (new OBC chain leads and CMRS date check)

### OBC Overseas Scholarship: two additional leads, neither promoted to a verified amendment

- A secondary archive lists **G.O.(Rt) No.69/2014/BCDD**, dated 18 August 2014, with the subject “Overseas Scholarship to OBC Students seeking admission in rated Foreign Universities - drawing & disbursing of Scholarship amount - sanctioned”. This appears operational/financial in nature. Its official PDF and operative text have not been retrieved; it is not yet classified as a policy amendment.
- A secondary archive describes **G.O.(Ms) No.03/2018/BCDD**, dated 9 April 2018, as enhancing the creamy-layer income limit. A Kerala High Court judgment in *Adhil M. Asif v. State of Kerala* (8 July 2019) lists the 2014 overseas scholarship parent order as petitioner exhibit P2 and the 2018 order as exhibit P3. The petition narrative concerned a request to raise the overseas scholarship family-income slab. This makes the 2018 order a potentially relevant lead, but does not establish that it amended the scholarship scheme. The actual order must be retrieved and read before making that claim.
- The 2019 judgment is a document-tracing aid only; it is not a substitute for either GO PDF.

Sources: [Sahayam October 2014 archive](https://www.sahayam.in/2014/10/); [Sahayam April 2018 archive](https://www.sahayam.in/2018/04/); [Adhil M. Asif v. State of Kerala](https://www.casemine.com/judgement/in/6431140090d8824f6459404d).

### CM Researcher Scholarship: order date discrepancy confirmed, not resolved

- The official HED 2025 index lists **G.O.(Ms) No.387/2025/HEDN** on 13 June 2025 as the original CM Research Scholarship guidelines.
- MGU Order No.6595/AC A6/2025/MGU, dated 18 July 2025, cites the same Government Order as dated 16 June 2025. The MGU order's operative provisions concern MGU's University Junior Research Fellowship, not CM Researcher Scholarship.
- The official HED index lists **G.O.(Ms) No.603/2025/HEDN** on 13 August 2025 and describes it as amending the CM-Researcher Scholarship guidelines for permanent research students.
- Neither full Government Order PDF was retrieved or inspected in this pass. The HED index entries verify order identifiers, dates as indexed, and subject descriptions only—not the operative clauses.

Sources: [Official HED 2025 GO index](https://highereducation.kerala.gov.in/index.php/103-hedn/government-order/g-o-index-for-2025); [MGU Order 6595/AC A6/2025/MGU](https://research.mgu.ac.in/wp-content/uploads/2025/07/6595-AC_A_6-2025-.-.-.pdf).

### Research classification rule retained

No new source in this pass qualifies as a verified gold amendment pair. Keep G.O.69/2014 and G.O.03/2018 as unverified OBC research leads; keep CMRS 387/2025 and 603/2025 as official-index-only entries until the actual complete PDFs and exact clause changes are inspected.


## Research update — 16 November 2026 (second pass: official OBC handbook and date cross-check)

### G.O.(Ms) No.03/2018/BCDD: identity corroborated, legal relevance narrowed

The official BCDD handbook published by the Director lists **G.O.(Ms) No.03/2018/BCDD dated 09.04.2018** in its table of contents (handbook page 101). The handbook is an official departmental publication, but the available text extraction did not yield a complete standalone copy of that GO. A secondary archive describes the order as “Creamy Layer Income Limit - Enhanced”.

The Kerala High Court judgment in *Adhil M. Asif v. State of Kerala* (08.07.2019) specifically concerns the OBC Overseas Scholarship and a request to raise its ₹6 lakh annual family-income ceiling. Its exhibit list includes the 2014 parent scholarship GO as P2 and the 2018 creamy-layer GO as P3. This is a useful explanation for why the two orders appear together in the case, but **it does not prove that the 2018 creamy-layer order amended the overseas scholarship guidelines**. Until the full 2018 GO is inspected, classify it as contextual/possibly relevant, not as a verified scholarship amendment.

Official departmental handbook: https://bcdd.kerala.gov.in/wp-content/uploads/2018/11/BCDD-Hand-book-pdf-1.pdf
Secondary subject description: https://www.sahayam.in/2018/04/
Judgment: https://www.casemine.com/judgement/in/6431140090d8824f6459404d

### G.O.(Rt) No.11/2014/BCDD: new date discrepancy in official application forms

The 2026 revised GO identifies the original parent as **G.O.(Rt) No.11/2014/BCDD dated 24.01.2014**. However, two official BCDD overseas-scholarship application forms (one hosted under `/2018/05/`, another under `/2020/11/`) cite the same GO as dated **29.1.2014**. These forms corroborate the order number and scheme linkage, but they are not the Government Order itself. Do not silently choose one date: record the 24 January date from the 2026 GO and the 29 January date from the official forms as an unresolved discrepancy pending retrieval of the parent PDF.

Official forms:
- https://bcdd.kerala.gov.in/wp-content/uploads/2018/05/05-03-APPLICATION-FORM-FOR-OVERSEAS-SCHOLARSHIP.pdf
- https://bcdd.kerala.gov.in/wp-content/uploads/2020/11/Application-Form.pdf

### Current research status

- 2014 parent G.O.11/2014/BCDD: not retrieved; official forms confirm the reference but disagree on its date.
- G.O.69/2014/BCDD: still only a secondary lead; no official operative text.
- G.O.03/2018/BCDD: identified in the official BCDD handbook index and as an exhibit in relevant litigation; full standalone order not retrieved and relationship to scholarship rules not established.
- CM Researcher G.O.387/2025 and G.O.603/2025: official HED index entries verified, full PDFs still not retrieved. The 13 June vs 16 June date discrepancy for G.O.387 remains unresolved.



## Research clarification — 16 November 2026 (OBC parent-order date conflict)
The date conflict is now recorded explicitly as an unresolved primary-source issue:
- G.O.(Rt) No.6/2026/BCDD identifies its cited parent, G.O.(Rt) No.11/2014/BCDD, as dated **24.01.2014**. Official PDF: https://document.kerala.gov.in/documents/governmentorders/govtorder2001202616%3A43%3A12.pdf
- Two official BCDD application forms independently print the parent order date as **29.1.2014**: https://bcdd.kerala.gov.in/wp-content/uploads/2018/05/05-03-APPLICATION-FORM-FOR-OVERSEAS-SCHOLARSHIP.pdf and https://bcdd.kerala.gov.in/wp-content/uploads/2020/11/Application-Form.pdf
- These references establish a genuine metadata discrepancy, not which date is correct. The original signed/issued G.O. PDF remains the authority needed to resolve it. Do not normalize the date or infer two different orders.
- A fresh official-domain search did not surface the complete 2014 PDF; the 2026 revised order remains the only retrieved official GO text in this branch.

## Engineering checkpoint — 16 November 2026
The deterministic eligibility evaluator now has explicit reviewed aliases for degree-level labels (for example, applicant `PG` against extracted `Postgraduate Degree programmes`, and `Ph.D` against `Research (PhD) programmes`). This is exact alias normalization, not fuzzy matching. Three regression tests cover the positive mappings and a negative unrelated-label case. Backend suite: **31 passed**; Python compilation passed.


## New official chain lead — G.O.(Rt) No.08/2022/BCDD

The official E-Grantz PDF for **G.O.(Rt) No.08/2022/BCDD dated 16 February 2022** has now been located and its searchable text reviewed: https://egrantz.kerala.gov.in/GO-8-2022-Overseas-selection-of-applicants_rearranged.pdf. Its preamble cites both **G.O.(Rt) No.11/2014/BCDD dated 24.01.2014** and **G.O.(Rt) No.39/2021/BCDD dated 24.05.2021**. It says the 2014 order established the scheme standards, that the scheme originally covered THE top-200 universities and was later expanded to top 600, and then records the 2021–22 beneficiary-selection context.

This gives us a stronger official lead for the intervening chain: retrieve and inspect **G.O.(Rt) No.39/2021/BCDD** next. The 2022 document is still a beneficiary-selection order; it does not replace the original 2014 guidelines or establish the complete amendment chain. Keep it out of the gold direct-amendment pair dataset.
