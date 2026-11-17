# Vignan Vidyanikethan AI — Science Fair Presentation Notes

**For:** explaining the student's website and preparing for questions after the Viksit Bharat essay. These are preparation notes—not evidence of selection or an INSPIRE-MANAK award.

## Read this first: what was actually checked

- Website supplied by the student: <https://VignanVidyanikethanAI.onrender.com/>. It initially showed Render's **“Application loading / service waking up”** page; a later page fetch displayed the app and its stated features, including uploaded materials, citations, quizzes and flashcards. Its [judge page](https://vignanvidyanikethanai.onrender.com/judge.html) also loaded. These are visible page descriptions, **not interactive verification** of answers, citations or offline behaviour. Test on your own device.
- A same-named public project repository was found: [Vignan Vidyanikethan AI on GitHub](https://github.com/Techno-projects-cpu/Vignan-Vidyanikethan-AI). Its README and `judge.html` describe the features below. **Repository documentation is not proof that the Render URL is running the same revision or that every feature works on your device.** Confirm and test the actual deployment before using specific claims in a presentation.
- The repository README says the project was developed with an AI coding agent under the student's direction and uses existing models; it is **not a model trained from scratch**. Present your own role and any teammates' contributions truthfully. [Project README](https://github.com/Techno-projects-cpu/Vignan-Vidyanikethan-AI/blob/main/README.md) · [Judge page source](https://github.com/Techno-projects-cpu/Vignan-Vidyanikethan-AI/blob/main/judge.html)
- INSPIRE-MANAK values originality, social applicability, user-friendliness and comparison with existing solutions. A science-fair presentation is **not itself proof** of nomination, selection or an award. [Official programme page](https://www.inspireawards-dst.gov.in/userp/award.aspx) · [Official teachers' handbook](https://inspireawards-dst.gov.in/download/others/Teachers-Handbook-for-nurturing-students-English.pdf)

**Before presenting:** fill in what you personally observed, ask your teacher about the fair's rules and timing, and remove any feature below that you cannot demonstrate or explain.

## 1. The project in one sentence

> “Vignan Vidyanikethan AI is a student-directed study-assistant project designed to help learners ask questions about their study material, check the sources and practise what they learn.”

**Important:** This sentence describes the public repository's stated design; confirm that it matches your deployed site and your own intent.

## 2. Problem → idea → proposed benefit

- **Problem:** A student may need an explanation suited to their own learning material, or may receive a fluent AI answer without knowing where it came from.
- **Idea:** Search relevant passages in the student's material, show an answer with a reference, and let the student check the cited page.
- **Proposed benefit:** Help students revise more independently and check evidence. A citation is a useful starting point, **not a guarantee** that an answer is correct or that the cited source itself is accurate.
- **Extra challenge:** Internet and AI services may be unreliable; the repository describes an offline/extractive option after preparation. Its availability depends on the actual device, prior setup, cached materials and deployment.

## 3. What the project README says it can do

**These are documented features, not features verified in the live Render deployment:**

1. **Library and retrieval:** add study material and find relevant passages. The README describes text/PDF ingestion and page-preserving citations; formats and page numbering should be tested with the exact material you intend to use.
2. **Source-based answers:** show book/page references so students can open the source and check it. An unsupported question may be refused or offered a clearly labelled outside-source route; test exactly what the live version does.
3. **Practice:** generate or assemble quizzes, flashcards and study tools around available material. Verify a specific activity before promising it to a judge.
4. **Several answer paths:** documentation describes an extractive fallback, optional cloud providers and a local model option. They are **not the same thing**: extractive answers use passages, while a local or cloud model can generate text.
5. **Offline design:** documentation describes caching an app shell and using saved material offline after setup. Internet search, some account features and cloud models require a connection; first-time model download also requires internet. Test on the actual demo device.
6. **Accessibility and language:** the repository documents interface language choices; check the exact languages and quality on the version you present instead of promising every language or perfect translation.

**Books:** The README says the starter shelf is project-written and real books can be added; it does not claim that publishers' textbook scans are bundled. Upload only material you have permission to use and avoid sensitive student information in demos.

## 4. How it works—explain without jargon

**Student question → find relevant material → make or extract an answer → show the source → student checks it.**

1. A student asks a question.
2. The app searches its available material for passages related to the question. This is **retrieval**—finding information, not teaching a model new knowledge permanently.
3. Depending on the chosen and available mode, it can display extracted material or use an existing model to compose a response based on that material.
4. The app shows a citation so the student can compare the answer with the relevant material.
5. If the answer or citation is wrong, that is a limitation or bug to report—not proof that the AI is always correct.

**What is AI here?** An existing model can generate text by identifying patterns learned during its training. Your project combines such tools with retrieval, an interface and source checking. A retrieval index or a rule-based extractive answer is useful software, but it is **not itself necessarily a generative AI model**.

## 5. A 60-second presentation — adapt after testing

“Good morning. My project is called Vignan Vidyanikethan AI. I wanted to explore how technology could make studying more accessible and help students check what an AI answer is based on.

The idea is to use the student's learning material as a source. When a question is asked, the system looks for relevant passages and can show an answer with a reference. The student should open the source and check it instead of trusting the answer blindly. The project also describes practice tools such as quizzes and flashcards.

This is not an AI model I trained from scratch. The website combines existing tools with a study interface and source-based workflow, and it was developed with an AI coding agent under my direction. Its limitations include possible incorrect answers, device requirements and features that depend on internet or prior setup. My aim is a useful, verifiable learning tool—not a replacement for teachers.”

**Personalise honestly:** Replace “I wanted” and the description of your role with your real experience. If classmates or teachers contributed, acknowledge them.

## 6. A demonstration that judges can verify

**Before the fair:** test every step on the actual device and version; use a short sample passage you wrote yourself. If anything fails, show what works and explain what remains to be fixed.

1. Open the website and select guest access if it is available.
2. Add a short, non-private sample passage with an easy-to-check fact, for example: “A triangle has three sides.” Use the text input only if the tested version supports it.
3. Ask: “How many sides does a triangle have?”
4. Point to the answer and its source, then open the source and compare it with the passage. If the citation is missing or incorrect, say so.
5. If available, show one quiz or flashcard based on that same material.
6. Optional: ask a question absent from the material and observe the actual response. Explain any refusal or outside-source label you actually see; do not promise a particular result without testing.

### Backup plan

- Render showed a waking-up page during the independent check. Open the site early, allow time for it to wake and check again on the fair's connection.
- Save **screenshots or a short recording of a real, successful test**, with no private information. Label them as a recording, not a live demo.
- If you intend to demonstrate offline use, first load and prepare the app and materials on that same device, then test airplane mode and reload yourself. Do not claim offline works if you haven't confirmed it.
- Have a printed flow diagram: **Question → relevant material → answer → citation → student checks**. A diagram is a fallback explanation, not a substitute for evidence of live operation.

## 7. Judge questions and honest answers

**Q: What problem are you solving?**
A: Students may need help understanding their own material and checking where an answer comes from. This project explores a source-based study workflow.

**Q: Did you train your own model?**
A: No. The project uses existing models or an extractive fallback; its work is in the interface, retrieval, source-based workflow and integration. Describe the path you actually demonstrate.

**Q: Did you write every line?**
A: The repository says an AI coding agent wrote code and tests under the student's direction. Explain your actual contributions, your collaborators' work and the assistance you used. Never claim work you did not do.

**Q: Is this just an AI wrapper?**
A: It uses existing models, so integration is part of it. The intended contribution is tying responses to study material and enabling source checking, with fallback and learning tools. Similar tools exist; explain what your project actually does differently, and do not claim to be the world's first without evidence.

**Q: Can it hallucinate?**
A: Yes, generated answers can be wrong or unsupported. A citation helps users inspect evidence, but even citations can be wrong or irrelevant. Verify against the source and a teacher.

**Q: Is it completely offline?**
A: The repository describes offline capabilities after preparation, but not every feature works offline. Model downloads, web search, accounts or cloud providers may need internet; confirm your device's actual behaviour.

**Q: Does it cost nothing for everyone forever?**
A: Do not promise that. Hosting, model downloads, mobile data, device requirements and free-tier limits can impose costs or restrictions. Explain what you actually paid and what remains conditional.

**Q: Is student data private?**
A: It depends on the selected mode. On-device processing and cloud processing differ; a cloud request may send text to a provider. Don't upload private information for a public demo, and read the actual privacy policy and provider terms. No untested system should be called perfectly secure.

**Q: Can it replace a teacher?**
A: No. It is a study aid. Teachers provide guidance, context and correction; students should verify answers.

**Q: What is original about it?**
A: Clearly explain your own design choices, the particular student problem and the evidence you have. Compare with existing study assistants honestly. An idea is not automatically novel just because a website exists.

## 8. What to establish before the presentation

- [ ] Is the GitHub repository linked above the exact source for your Render site? Which version is running?
- [ ] What specific features work on your phone/computer today? Which need internet or setup?
- [ ] What problem did **you** personally notice, and whom does it help?
- [ ] What did you decide, design, test and build? What assistance did the AI agent, teachers or teammates provide?
- [ ] Have you tested a citation, a question missing from the material and your chosen fallback?
- [ ] Have you obtained permission for demo materials and excluded private information?
- [ ] Are your sample results real and recorded, without invented user counts, marks, statistics or awards?
- [ ] How is this project different from existing tools, and what is still unproven?

## Sources

1. [Project repository README](https://github.com/Techno-projects-cpu/Vignan-Vidyanikethan-AI/blob/main/README.md) — description and limitations of the source repository; deployment may differ.
2. [Project judge page source](https://github.com/Techno-projects-cpu/Vignan-Vidyanikethan-AI/blob/main/judge.html) — documented pitch and test suggestions, not independently reproduced here.
3. [INSPIRE-MANAK official overview](https://www.inspireawards-dst.gov.in/userp/award.aspx) — programme aims and evaluation considerations.
4. [INSPIRE-MANAK teachers' handbook](https://inspireawards-dst.gov.in/download/others/Teachers-Handbook-for-nurturing-students-English.pdf) — innovation, social relevance and developing ideas. Some programme details can change; consult the current official notice.
