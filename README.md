# AI Job Application Agent

**AI Job Application Agent** is an automated, AI-powered orchestrator designed to streamline and automate the process of applying for jobs. Given a candidate's profile, resume, and a job posting URL, the system scrapes the job description, evaluates the candidate's fit, generates tailored application materials, and automatically fills out Applicant Tracking System (ATS) forms (like Greenhouse). 

## 🎯 Key Features

- **Automated Job Scraping & Parsing:** Uses Playwright to navigate to job URLs and extract relevant job descriptions and ATS platform details.
- **Intelligent Triage & Evaluation:** Uses Large Language Models (LLMs) to evaluate the candidate's resume against the job description. Only proceeds with the application if a defined match score (e.g., ≥ 60%) is met.
- **Dynamic Asset Generation:** Tailors the candidate's resume and drafts a specific cover letter specifically for the targeted role.
- **Automated Form Filling:** Drives a headless browser to automatically fill out ATS web forms using the candidate's profile and custom answers to standard ATS questions (e.g., sponsorship requirements).
- **Human-in-the-Loop (HITL) Fallback:** Hands off complex, unknown, or visually complex fields to a human supervisor for manual intervention seamlessly.
- **Persistent Storage:** Uses PostgreSQL to track candidate profiles, job application queues, and custom answers to common questions.

## 🏗️ Architecture & Workflow

The application leverages an agentic state-machine architecture driven by **LangGraph**. The workflow processes applications asynchronously through multiple specialized nodes:

1. **Onboarding / Parsing:** Loads the candidate's core profile and resume.
2. **Scraping:** Navigates to the job URL to extract the job description.
3. **Triage:** Evaluates the candidate against the role. Routes to application filling if it's a good match, otherwise skips.
4. **Asset Generation:** Creates a tailored resume and cover letter.
5. **Browser Automation:** Fills out the ATS web forms autonomously.
6. **Human Fallback:** Hands off to a human for incomplete or complex fields.
7. **Logging:** Saves the final execution status and records any errors.

## 💻 Tech Stack

- **Workflow Orchestration:** [LangGraph](https://python.langchain.com/docs/langgraph) & LangChain Core
- **LLM Integration:** `langchain-google-genai` (Google's Gemini models for evaluation and text generation)
- **Web Scraping & Automation:** [Playwright](https://playwright.dev/python/) (async form-filling and site navigation)
- **Database & ORM:** PostgreSQL & SQLAlchemy 
- **Infrastructure:** Docker & Docker Compose (for the local Database setup)

## 📋 Prerequisites

- Python 3.10+
- Docker and Docker Compose (to run the PostgreSQL database)
- Playwright browsers installed
- Google Gemini API Key

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/AI_Job_Application_Agent.git
cd AI_Job_Application_Agent
```

### 2. Start the Database
The application relies on PostgreSQL to store profiles and job queues. Start the database service natively or via Docker:
```bash
docker-compose up -d
```

### 3. Install Dependencies
Create a virtual environment, install the required packages, and install the Playwright browser binaries:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
playwright install
```

### 4. Configuration
Create a `.env` file in the root directory (you can use a `.env.example` as a template if available) and add your environment variables:
```env
# Example .env configuration
GOOGLE_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### 5. Add Candidate Data
Place your base resume in the `data/resumes/` folder as a text or PDF file (depending on your setup). Ensure the local database is populated with the Candidate Profile and standard Custom Answers.

### 6. Run the Agent
Execute the main application orchestrator to kick off the pipeline:
```bash
python src/main.py
```

## 📁 Project Structure

```text
AI_Job_Application_Agent/
├── docker-compose.yml       # Database infrastructure setup
├── requirements.txt         # Python dependencies
├── data/
│   └── resumes/             # Candidate resumes and base assets
├── src/
│   ├── main.py              # Orchestrator & LangGraph setup
│   ├── models.py            # SQLAlchemy database models
│   ├── state.py             # LangGraph state definitions
│   ├── ats_adapters/        # Platform-specific form filling strategies
│   │   ├── base.py
│   │   └── greenhouse.py
│   └── nodes/               # LangGraph workflow nodes
│       ├── agent_nodes.py
│       ├── browser_automator.py
│       └── hitl.py          # Human-in-the-loop interfaces
└── tests/                   # Pytest test suite
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
