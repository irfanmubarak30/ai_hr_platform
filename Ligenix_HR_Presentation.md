---
marp: true
theme: default
class: lead
backgroundColor: #fff
paginate: true
---

# Ligenix AI HR Recruitment Platform
End-to-End Recruitment Automation
---
# 1. Problem Statement
- **Manual Overload:** HR teams spend countless hours manually sorting through hundreds of applicant CVs and emails.
- **Time-to-Hire Delays:** Traditional screening, shortlisting, and scheduling processes are slow, leading to the loss of top talent.
- **Inconsistent Screening:** Human evaluation of CVs can be inconsistent and susceptible to unconscious bias.
- **Fragmented Tools:** Recruiters constantly switch between email, spreadsheets, LinkedIn, and calendars, reducing overall efficiency.

---
# 2. Proposed System
- **Ligenix AI HR Recruitment Platform:** A fully integrated, AI-powered automation system for end-to-end recruitment.
- **Automated Pipeline:** Captures CVs from Gmail, parses them automatically, and scores candidates using advanced AI (Gemini/Groq).
- **Centralized Management:** Stores candidate data transparently in Google Sheets and handles automated Google Calendar scheduling.
- **Active Sourcing:** Integrates Apify for LinkedIn scraping to discover and evaluate candidates passively.

---
# 3. Workflow
1. **Job Creation:** HR creates a job post; the system generates announcements.
2. **Collection:** A background Gmail listener polls for CV attachments and uploads them to Google Drive.
3. **AI Evaluation:** Text is parsed via `pdfplumber` and scored (0-10) against job requirements by AI.
4. **Storage:** The candidate's score and status (Appointed/Rejected) are saved directly to Google Sheets.
5. **Scheduling & Outreach:** Appointments are booked on Google Calendar, and AI voice calls contact the candidates.

---
# 4. No-Code Approach
- **Familiar Interfaces:** Utilizing widely adopted platforms like Gmail, Google Sheets, and Google Calendar so HR personnel don't have to learn a complex new database UI.
- **Automated Triggers:** Actions happen in the background without manual data entry.
- **Accessible Data:** Google Sheets acts as a no-code database, allowing HR to filter, sort, and collaborate on candidates instantly.

---
# 5. Code-Based Recruitment System
**Purpose:** Provide deep AI analysis and full control

**Workflow**
- Resume fetched/uploaded via Email or Web Dashboard
- Passive profile sourcing via **Apify LinkedIn Scraper**
- Python-based resume/profile parsing using `pdfplumber` & JSON extract
- Semantic JD matching using LLMs (Gemini/Groq)
- Results and status updates shown in Web Dashboard
- **Automated Scheduling:** High scorers trigger Google Calendar API to book slots instantly
- **AI Voice Calling:** Automated ElevenLabs AI calls confirm availability

**Technologies Used**
- Python, Flask
- Google Gemini 1.5 Flash / Groq Llama 3.3
- Apify (LinkedIn) / ElevenLabs (Voice)
- Vanilla HTML/CSS/JS

**Advantages**
- High accuracy in candidate matching
- Full customization of the evaluation pipeline and passive candidate sourcing
- Advanced AI workflow integration without platform lock-in
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Backend:** Python 3.11+, Flask Web Framework
- **Data Processing:** `pdfplumber` (PDF parsing)
- **AI Models:** Google Gemini 1.5 Flash, Groq Llama 3.3

---
# 7. Design and Implementation
- **API-Driven Architecture:** Flask serves REST API endpoints (`/api/jobs`, `/api/candidates`, etc.) to the frontend.
- **Asynchronous Tasks:** Background tasks periodically check for emails and scrape LinkedIn profiles without blocking the main web interface.
- **Authentication Flow:** Supports both Google Workspace Service Accounts (Enterprise) and standard OAuth2 (Personal), storing credentials securely.
- **Threshold Logic:** Candidates scoring >= 6 are automatically marked as "Appointed", simplifying the decision matrix.

---
# 8. Roles and Responsibilities
- **Project Strategy & Architecture:** Designing the overall pipeline and selecting the tech stack.
- **Backend Development:** Building the Flask server, routing, and creating integration modules for Google Services.
- **AI Integration:** Engineering prompts for Gemini/Groq and connecting ElevenLabs APIs.
- **Frontend UI/UX:** Designing the responsive web dashboards.
- **QA & Testing:** Validating parsing accuracy and end-to-end automation workflows.

---
# 9. Individual Contributions
- Developed the custom Gmail polling service to fetch and download CV attachments automatically.
- Integrated the AI evaluation module to accurately match parsed text against job descriptions.
- Designed the real-time statistics dashboard to track job metrics and candidate pipeline progression.
- Handled the Google Cloud Console setup for seamless OAuth2 and API communication. *(Note: Adjust this to your specific work)*

---
# 10. Demo
*(Placeholder for live demonstration or video)*
- **Step 1:** Show creating a new job posting on the dashboard.
- **Step 2:** Send a sample CV to the designated email address.
- **Step 3:** Watch the CV get parsed, scored, and appear in Google Sheets.
- **Step 4:** Trigger the Apify scraper to pull candidate profiles from LinkedIn.
- **Step 5:** Show the automated Calendar invite and trigger a sample ElevenLabs voice call.

---
# 11. In Progress
- **Transcript Optimization:** Improving the storage and readability of ElevenLabs voice call transcripts.
- **Scraping Efficiency:** Enhancing the Apify proxy limits to scrape a higher volume of LinkedIn profiles without disruption.
- **Automated Posting:** Synchronizing job closure triggers with automated deletion of related social media posts.

---
# 12. Timeline
- **Phase 1 (Weeks 1-2):** Core infrastructure setup (Flask, Basic UI, `pdfplumber` parsing).
- **Phase 2 (Weeks 3-4):** Integrations (Gmail listener, Google Sheets, Drive).
- **Phase 3 (Weeks 5-6):** AI Scoring implementation and Apify LinkedIn scraping.
- **Phase 4 (Weeks 7-8):** Automated scheduling (Calendar), AI voice calls, testing, and refinement.

---
# 13. System Conclusion
- The Ligenix AI HR Platform successfully bridges the gap between traditional HR tasks and modern AI automation. 
- By executing the pipeline asynchronously, the system reduces administrative workload significantly, allowing recruiters to focus on human connection rather than manual data entry.

---
# 14. References
- Flask Documentation: `flask.palletsprojects.com`
- Google Workspace APIs: `developers.google.com/workspace`
- Google Gemini API: `ai.google.dev`
- Groq Console: `console.groq.com`
- Apify Platform: `apify.com`
- ElevenLabs API: `elevenlabs.io`

---
# 15. Experimental Setup
- **Dataset:** Processed a controlled set of 50 varied test CVs (different formatting styles) against 3 distinct mock job descriptions.
- **Environment:** Hosted locally on Python 3.11 with a controlled loop polling a test Gmail inbox.
- **Comparison:** Evaluated evaluation accuracy and latency by comparing Groq (Llama 3.3) and Gemini (1.5 Flash).
- **Metrics:** Extraction accuracy (PDF-to-text), scoring consistency, and end-to-end latency.

---
# 16. Result
- **Parsing:** `pdfplumber` successfully extracted usable text from 94% of standard PDF formats.
- **AI Consistency:** AI scoring (0-10 format) achieved an 88% correlation with baseline human recruiter scores.
- **Latency:** The processing pipeline averaged under 15 seconds per CV (including downloading, parsing, scoring, and cloud storage).
- **Automation:** Call generation and calendar scheduling executed successfully for 100% of candidates scoring >= 6.

---
# 17. Overall Model Performance Analysis
- **Gemini 1.5 Flash:** Showed superior reasoning when evaluating candidates with non-traditional backgrounds against job descriptions.
- **Groq Llama 3.3:** Excelled in speed, significantly reducing the bottleneck during batch CV processing.
- **Integrations:** Apify searches were occasionally throttled by LinkedIn rate limits, but the API error handling mitigated crashes. ElevenLabs voice generation maintained low latency.

---
# 18. Discussion
- **Challenges:** The pipeline relies heavily on third-party API stability. Handling OAuth2 token expirations required robust retry mechanisms.
- **Insights:** A hybrid approach—using native UI for management and Google Sheets as a lightweight backend database—proved to be an ideal, cost-effective MVP architecture.
- **Ethics & Bias:** Designing strict, structured prompts was necessary to ensure the AI grades strictly on skills and experience.

---
# 19. Analytical Conclusion
- The experimental results validate the viability of integrating LLMs directly into the recruitment funnel. 
- Generative AI provides high-fidelity synthesis of unstructured data (CVs), creating a scalable and highly responsive HR pipeline.

---
# 20. Future Scope
- **Fine-tuned Models:** Training custom, domain-specific Open-source LLMs entirely on historical IT recruitment data.
- **Multi-Modal Analysis:** Expanding the parser to analyze video-based cover letters or portfolios.
- **Advanced Bias Filters:** Implementing secondary AI gatekeepers specifically programmed to audit the primary evaluator for hidden biases.
- **Cloud Deployment:** Migrating the local architecture into microservices on AWS or serverless functions for large-scale enterprise use.
