# Autonomous LinkedIn Easy Apply AI Agent

An **AI-powered autonomous job application agent** built with **Python, Playwright, and OpenAI-compatible LLM APIs**. The agent searches LinkedIn for relevant opportunities, evaluates candidate-job fit using generative AI, and automates multi-step **LinkedIn Easy Apply** workflows.

> ⚠️ **Disclaimer:** This project is intended for educational and research purposes. Use browser automation responsibly and ensure your usage complies with LinkedIn's Terms of Service and applicable policies.

---

## Key Features

### Autonomous Job Discovery

* Searches LinkedIn for jobs based on configured criteria.
* Extracts job title, company, description, and other relevant metadata.
* Evaluates opportunities against the candidate's resume/profile before applying.

### Multi-Provider LLM Fallback Router

* Uses a hierarchical inference strategy:
  **Groq → OpenRouter → Local Ollama**
* Automatically falls back to another provider when an upstream provider encounters rate limits, quota issues, or availability problems.
* Uses the **OpenAI SDK** for a consistent interface across compatible providers.

### 5-Strategy DOM Detection Pipeline

Uses multiple detection strategies to handle LinkedIn's dynamic UI:

1. ARIA labels and accessibility attributes
2. Semantic roles
3. Fuzzy text matching
4. DOM/action-area inspection
5. iframe detection and interaction

This makes the automation more resilient to changes in page structure and element positioning.

### Intelligent Multi-Step Form Automation

* Traverses multi-page Easy Apply forms.
* Automatically fills text fields.
* Handles dropdowns, radio buttons, and common application fields.
* Uses LLM-generated responses for custom open-ended questions.
* Maintains application state while navigating through form steps.

### Resilient Browser Automation

* Browser lifecycle validation using session/browser health checks.
* Handles dynamically rendered content through DOM hydration and scrolling.
* Includes metadata extraction fallbacks to reduce failed job parsing.
* Detects unexpected redirects, browser-context failures, and interrupted sessions.

---

## Technical Architecture

```text
                         ┌──────────────────────┐
                         │      agent.py        │
                         │   Main Orchestrator  │
                         └──────────┬───────────┘
                                    │
                   ┌────────────────┴────────────────┐
                   │                                 │
                   ▼                                 ▼
        ┌─────────────────────┐          ┌─────────────────────┐
        │  LinkedIn Engine    │          │  LLM Router         │
        │  src/linkedin.py    │          │  src/gemini.py      │
        └──────────┬──────────┘          └──────────┬──────────┘
                   │                                 │
        ┌──────────┴──────────┐          ┌───────────┼───────────┐
        │                     │          │           │           │
        ▼                     ▼          ▼           ▼           ▼
   Job Search &          Easy Apply   Groq     OpenRouter    Ollama
   Metadata              Form Engine  Cloud      Cloud        Local
   Extraction
```

### Application Flow

```text
LinkedIn Search
       │
       ▼
Collect Job Listings
       │
       ▼
Extract Job Metadata
       │
       ▼
Load Candidate Resume/Profile
       │
       ▼
LLM-Based Job Fit Evaluation
       │
   ┌───┴────┐
   │        │
Reject    Match
   │        │
   ▼        ▼
Skip Job   Open Easy Apply
            │
            ▼
      Detect Form Elements
            │
            ▼
       Fill Application
            │
            ▼
     Generate AI Answers
            │
            ▼
       Submit / Log Result
```

---

## Tech Stack

| Category               | Technologies     |
| ---------------------- | ---------------- |
| **Language**           | Python 3.10+     |
| **Browser Automation** | Playwright       |
| **LLM Integration**    | OpenAI SDK       |
| **Cloud LLMs**         | Groq, OpenRouter |
| **Local LLM**          | Ollama           |
| **PDF Processing**     | PyMuPDF          |
| **Data Validation**    | Pydantic         |
| **Configuration**      | python-dotenv    |
| **Data Storage**       | JSON             |

---

## Repository Structure

```text
linkedin-job-agent/
│
├── agent.py                    # Main execution and orchestration
│
├── src/
│   ├── linkedin.py             # LinkedIn automation engine
│   ├── gemini.py               # LLM provider routing and prompts
│   ├── resume.py               # Resume parsing and profile extraction
│   └── jobs.py                 # Job and matching data models
│
├── data/
│   ├── applications.json       # Application history
│   └── skipped_jobs.json       # Skipped/processed jobs
│
├── .env                        # Environment variables (not committed)
├── .gitignore
└── README.md
```

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/DevendraKalmodiya/JobHunt.git
cd linkedin-job-agent
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install playwright openai python-dotenv pymupdf pydantic
```

Install the Playwright browser:

```bash
playwright install chromium
```

---

## Environment Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

If using a local Ollama instance, ensure Ollama is installed and running locally.

> **Never commit your `.env` file or API keys to GitHub.**

Add the following to `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

---

## Resume Configuration

Place your resume PDF in the location expected by the project configuration.

The resume parser extracts relevant candidate information and converts it into a structured profile used during job-fit evaluation and application generation.

---

## Running the Agent

Start the application with:

```bash
python agent.py
```

The agent then orchestrates the workflow:

```text
Search → Extract → Evaluate → Apply → Log
```

Application and skipped-job information can be persisted in the `data/` directory.

---

## LLM Provider Strategy

The project uses a fallback architecture to improve inference reliability:

```text
                 ┌─────────────┐
                 │ LLM Request │
                 └──────┬──────┘
                        │
                        ▼
                ┌───────────────┐
                │     Groq      │
                └──────┬────────┘
                       │ Failure / Limit
                       ▼
                ┌───────────────┐
                │  OpenRouter   │
                └──────┬────────┘
                       │ Failure / Limit
                       ▼
                ┌───────────────┐
                │    Ollama     │
                │  Local Model  │
                └───────────────┘
```

This architecture allows the application to continue operating even when an individual cloud provider becomes unavailable or reaches its usage limit.

---

## Security Considerations

* Keep API credentials exclusively in environment variables.
* Never commit `.env` to version control.
* Do not store LinkedIn credentials directly in source code.
* Review application logs before publishing the repository.
* Use a dedicated browser profile/session where appropriate.
* Respect LinkedIn's terms, rate limits, and anti-automation policies.

---

## Current Limitations

* LinkedIn's UI and DOM structure can change without notice.
* Some applications contain custom questions or workflows that require additional handling.
* CAPTCHA, verification challenges, and authentication interruptions may require manual intervention.
* LLM-generated answers should be reviewed for accuracy before submission.
* Browser automation reliability depends on network conditions and page changes.

---

## Future Improvements

* [ ] Job deduplication and intelligent prioritization
* [ ] Configurable job search profiles
* [ ] Application success/failure analytics
* [ ] Web dashboard for monitoring applications
* [ ] Structured application database
* [ ] Better handling of complex/custom form components
* [ ] Screenshot-based UI element detection
* [ ] Application scoring and ranking dashboard
* [ ] Automated retry and recovery workflows

---

## Engineering Highlights

This project demonstrates practical implementation of:

* **Browser automation and web interaction**
* **LLM orchestration and provider abstraction**
* **Fallback architecture and fault tolerance**
* **Dynamic DOM element detection**
* **Stateful workflow automation**
* **Resume parsing and structured data extraction**
* **AI-based semantic matching**
* **Robust error and session handling**

---

## Contributing

Contributions, improvements, and ideas are welcome. Feel free to open an issue or submit a pull request.

---

**Built with Python 🐍 · Playwright 🎭 · LLMs 🧠**
