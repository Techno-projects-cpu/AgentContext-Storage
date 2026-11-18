# Vignan Vidyanikethan AI: Deep Technical and Judge Workbook

**Purpose:** Understand the science behind your project, defend your design honestly, and collect evidence before the fair. Start with [the pitch and demonstration notes](01-website-presentation-notes.md). The deployed site's pages and public repository describe features, but page fetching did **not** independently test them interactively. Confirm your live version and exact role yourself. Don't claim a feature, result, award or novelty you cannot support.

## ★ One-minute mental model

**User's material → text extraction → smaller passages → search/index → relevant evidence → extract or generate an answer → citation → human checks.**

Some routes depend on a model and some do not. The repository describes an extractive fallback, optional existing cloud/local models and a cache-based offline design. A well-designed system should label the origin of an answer and its limits. Existing tools do similar things: the meaningful question is whether your chosen design helps its users in a demonstrable way.

## 1. What problem is this actually solving?

General-purpose chatbots may give plausible but unsupported answers. A learner may instead want an answer based on a specific set of notes or pages and a way to inspect those pages. The project **aims** to shorten the path from question to evidence and practice. This is a design objective, not proof that learners improve their marks.

**Scientific framing:**
- Need: “Can students locate and check evidence in their own learning material more conveniently?”
- Proposed intervention: retrieval plus citations, with study tools.
- Observable outcomes: whether a cited passage is relevant, whether its page number is correct, and whether users can find it.
- Limitations: poor scans, missing information, irrelevant retrieval, wrong answers, device constraints and unreliable connectivity.

A test of citation accuracy is not automatically a test of educational improvement. Showing improved learning would require a properly designed, consent-based study, not a single impressive demo.

## 2. How retrieval works

1. **Input and extraction:** a readable PDF, text or notes become searchable text. Image-only pages may need OCR, and layout, tables or equations may extract badly. Test your exact file.
2. **Chunking:** divide text into passages small enough to search and use. Tiny chunks may lose context; huge chunks can add irrelevant text and increase processing cost. Preserve document identity and page metadata when possible.
3. **Index:** store a searchable representation. Keyword search finds matching words; a vector/embedding-based search can represent semantic similarity. Similarity is not the same as truth or proof. Do not assert a specific implementation unless you have checked it in the code or current version.
4. **Retrieval:** rank passages related to the user's question. The best-ranked passage can still be wrong, incomplete or outdated.
5. **Response:** an extractive path may quote or select text. A generative model may produce an explanation from retrieved context; it can still invent facts or misunderstand a source.
6. **Citation and checking:** link the answer to the original passage and page. Check both that the page exists and that it actually supports the claim. A real citation to an unrelated passage is still a bad answer.

This general pattern is often called **retrieval-augmented generation (RAG)** when retrieval supplies context to a generative model. A purely extractive fallback can use retrieval without generation, so do not call every response generative AI.

## 3. AI terms judges may ask about

- **Model:** a learned system used to make predictions or generate outputs. This project uses existing models where configured; it is not a foundation model trained from scratch.
- **Inference:** running a trained model to produce an output. **Training:** adjusting model parameters using data. Retrieving an uploaded book at question time is not the same as retraining the model on that book.
- **Hallucination:** a generated claim that is false or unsupported. Grounding can reduce some failures but cannot guarantee correctness.
- **Context window:** the limited text a model can consider in one request. Retrieval selects useful passages rather than necessarily sending an entire library.
- **Prompt:** instructions and data supplied to a model. Text inside a source can contain hostile instructions; treat source text as data rather than authority. No prompt alone guarantees security.
- **Local vs cloud:** local processing can run on the user's device if supported and prepared; a cloud provider processes information sent over the network. “Local” does not automatically mean every part of the app stays local.
- **WebGPU:** a browser technology that may enable suitable local models on compatible hardware/browsers. Model downloads can be large and first-time setup can require internet. Check device support instead of promising universal compatibility.

## 4. ★ A fair, repeatable experiment

Use a **small evaluation set** of passages you wrote yourself or have permission to use. Record the exact build, device, date, network and settings. Illustrative questions below are invented test cases, not observed project results.

| Case | Material | Question | Expected check |
|---|---|---|---|
| Explicit fact | “The school garden has 12 pots.” | How many pots? | Answer agrees; source opens to that sentence. |
| Absent fact | Same sentence | What colour are the pots? | Observe whether it admits insufficient source evidence or clearly labels an outside route. |
| Similar but distinct | “A has 12 pots. B has 15 pots.” | How many does B have? | Check that it does not confuse A and B. |
| Page check | A two-page document, fact only on page 2 | Ask about the fact. | Inspect actual source and page number. |
| Unsupported premise | “A triangle has three sides.” | Why does a triangle have four sides? | Check that the response challenges or refuses the false premise. |

For each case record **actual answer, cited page and passage, whether supported, and any failure**. Turn web fallback on or off deliberately and record the setting; outside information must not be mistaken for a source-based answer.

**Example calculation only:** if 7 out of 10 attempted citations correctly point to supporting passages, observed citation support = 7/10 = 70%. This is an imaginary calculation, **not a project result**, and a tiny hand-picked sample cannot establish general accuracy. Include refusals and failures in your report; report the denominator and how you selected cases. Try paraphrases, conflicting passages and scanned PDFs if supported.

**Safe user study:** Ask teacher permission and use adult/guardian consent as required. Avoid collecting names, sensitive information or children's private data. A comparison with an ordinary search tool should use similar tasks and conditions. Do not announce an improvement until measurements support it.

## 5. Offline: a system with multiple dependencies

A website normally needs a network to fetch files. A **service worker** can cache an app shell and eligible resources for later use. Separately, saved books or indexes can remain on a device, subject to browser storage policies and user deletion. A local model, if used, may require an initial download and compatible hardware. A cloud model and web search need network access.

**Test plan:**
1. On the actual demo device, load the app and set up the intended books and mode while online.
2. If available, run the app's offline-readiness check and record what it reports.
3. Disconnect using airplane mode, then reload and run the planned question and practice activity.
4. Record which features worked or failed. Reconnect and retest. One device's result does not prove every phone works.

A successfully cached shell does not guarantee that all models, documents, APIs or accounts will be available offline. Browser storage may be cleared, and updates can change behavior. Never use a saved video as if it were a live test.

## 6. Privacy, security and responsible use

Make a **data-flow map** for the actual selected settings:

- What stays in this browser? What can be deleted? What might the browser evict?
- What goes to the app server, an account service, a search provider or an AI provider? Which settings change this?
- Does importing a public URL send it to a server? Could that URL contain secrets?
- What are the policies and age requirements? What information is visible to other users?

Only assert answers you've checked against the live app and its policies. Avoid uploading personal data or copyrighted material without permission. A citation does not make a source reliable; consult teachers and original references. An app that has not received an independent security audit should not be described as perfectly secure. Use a unique password and no private demo account details.

## 7. Design trade-offs and judge answers

**Why not train a new model?** Training a competitive model requires significant data, computing resources and evaluation. This project explores a different engineering problem: organising existing tools around a student's material and checking sources. The student directed the project and the repository states an AI coding agent wrote code and tests; describe your own contributions precisely.

**Is this just a wrapper?** It integrates existing components, so a wrapper description can be fair. Explain any retrieval, citation, offline and user-experience features you can actually demonstrate, and compare against existing study tools without claiming an unsupported first.

**What if the answer has a citation but is wrong?** The cited passage may not support the statement, extraction may fail, or the source itself may be mistaken. Open the cited page and verify. Record it as a failure if the reference does not support the answer.

**What if the internet goes down?** It depends on prior caching, mode and device; show a tested fallback. Cloud and live web features still require a connection.

**Is it free?** The project documents free-tier use, but plans, quotas, hosting, hardware, electricity and data can change or cost money. Describe your actual expenses and conditions rather than guaranteeing permanent free service.

**How is it different from other learning apps?** Make a comparison table using features you checked on the same date. A capability may already exist elsewhere. A particular design or focus can still be useful without being globally unique.

**What is the next improvement?** Depending on actual failures: more reliable page extraction, accessible design, citation evaluation, transparent data flows, or improved low-connectivity handling. Prioritise based on observed evidence, not invented user complaints.

## 8. Build your own evidence sheet

Fill this in after real testing, not from assumptions:

- **My specific idea / problem:** __________________________________
- **My decisions and work:** _______________________________________
- **AI agent, teachers and collaborators' contributions:** __________
- **App version, device, browser and date:** ________________________
- **Sample source and permission:** ________________________________
- **Question, answer, and supporting page:** ________________________
- **What failed or needs improvement:** _____________________________
- **Offline setup and observed result:** ____________________________
- **One similar existing solution and fair comparison:** ___________
- **One question I cannot yet answer:** _____________________________

## Sources to inspect

- [Project repository and README](https://github.com/Techno-projects-cpu/Vignan-Vidyanikethan-AI) and [judge page](https://vignanvidyanikethanai.onrender.com/judge.html): project claims, not independent validation.
- [INSPIRE-MANAK official programme](https://www.inspireawards-dst.gov.in/userp/award.aspx): programme context. Confirm current local participation requirements with your teacher.
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework): thinking systematically about AI risks and evaluation.
- [MDN: Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API): browser caching and offline concepts.
