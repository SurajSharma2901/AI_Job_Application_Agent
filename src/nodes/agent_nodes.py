import asyncio
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from src.state import ApplicationState, ParsedCandidate, TriageScore, TailoredAssets, FieldInference
import os

# --- LLM Utilities ---
def get_structured_llm(schema):
    """Returns a structured output LLM, prioritizing Gemini and falling back to Groq."""
    
    # We must provide Groq with a fallback model that exists
    groq = ChatGroq(temperature=0, model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
    groq_structured = groq.with_structured_output(schema)
    
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    if os.getenv("GEMINI_API_KEY"):
        try:
            gemini = ChatGoogleGenerativeAI(temperature=0, model=gemini_model, google_api_key=os.getenv("GEMINI_API_KEY"))
            gemini_structured = gemini.with_structured_output(schema)
            # The fallback wrapper
            return gemini_structured.with_fallbacks([groq_structured])
        except Exception:
            return groq_structured
            
    return groq_structured

# --- 1. Candidate Onboarding (Resume Parsing) ---
async def parse_resume_node(state: ApplicationState) -> ApplicationState:
    print("[Node] CandidateOnboarding: Parsing raw resume dynamically...")
    import PyPDF2
    
    resume_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'resumes', 'resume1.pdf'))
    if not os.path.exists(resume_path):
        print(f"[Error] Resume not found at: {resume_path}")
        return state
        
    text = ""
    try:
        with open(resume_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"[Error] reading PDF: {e}")
        return state
        
    llm = get_structured_llm(ParsedCandidate)
    prompt = PromptTemplate.from_template("""You are an expert technical recruiter and resume parser.
Extract structured information from the raw resume text provided below. Extract email, github and linkedin links exactly.

## Resume Text:
{raw_resume}
""")
    
    try:
        # Await the parsed result from the LLM
        try:
            parsed_result = await llm.ainvoke(prompt.format(raw_resume=text[:10000]))
        except Exception:
            # Absolute fallback to Groq if the fallback chain also bugs out with Google
            print("  [>] Gemini failed, manually falling back to Groq...")
            fallback_llm = get_structured_llm(ParsedCandidate).fallbacks[0]
            parsed_result = await fallback_llm.ainvoke(prompt.format(raw_resume=text[:10000]))
            
        # Save exact dict into state
        state["candidate_profile"] = parsed_result.model_dump()
        print(f"  [>] Parsed: {parsed_result.name}, {parsed_result.email}, {parsed_result.linkedin_url}")
    except Exception as e:
        print(f"[Error] Failed to parse: {e}")

    return state

# --- 2. Browser Scraper (Fetch JD) ---
async def browser_scraper_node(state: ApplicationState) -> ApplicationState:
    print(f"[Node] BrowserScraper: Fetching JD from {state['job_url']}")
    from playwright.async_api import async_playwright
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            response = await page.goto(state["job_url"], timeout=30000)
            
            # Simple ATS Detection by URL
            url = page.url
            ats_platform = "Unknown"
            if "greenhouse.io" in url:
                ats_platform = "Greenhouse"
            elif "jobs.lever.co" in url:
                ats_platform = "Lever"
            elif "myworkdayjobs.com" in url:
                ats_platform = "Workday"
            
            print(f"[Node] BrowserScraper: Detected ATS - {ats_platform}")
            
            # Extract main text
            text_content = await page.evaluate("document.body.innerText")
            
            state["job_description"] = text_content[:5000]  # Truncate to save tokens
            state["ats_platform"] = ats_platform
            
            await browser.close()
    except Exception as e:
        print(f"[Error in BrowserScraper]: {e}")
        state["job_description"] = "Failed to scrape JD."
        state["ats_platform"] = "Unknown"
        
    return state

# --- 3. Triage Agent (Match Scorer) ---
def triage_agent_node(state: ApplicationState) -> ApplicationState:
    print("[Node] TriageAgent: Scoring match...")
    llm = get_structured_llm(TriageScore)
    
    prompt = PromptTemplate.from_template("Rate how well the candidate matches the JD on a scale of 0-100.\nJD: {jd}")
    # score_result = llm.invoke(prompt.format(jd=state["job_description"]))
    
    # Example logic
    state["match_score"] = 85.0
    return state

# --- 4. Asset Generator (Tailoring) ---
def asset_generator_node(state: ApplicationState) -> ApplicationState:
    print("[Node] AssetGenerator: Tailoring resume and generating Cover Letter...")
    llm = get_structured_llm(TailoredAssets)
    
    # result = llm.invoke(...)
    state["tailored_resume_text"] = "Tailored bullets addressing Python, SQL, and AWS."
    state["cover_letter_text"] = "Dear Hiring Manager... I have expert Python skills."
    return state

# --- 5. Browser Automator & 6. Form Filler & 7. HITL ---
# (Combined placeholder for the multi-step browser interaction)
async def form_filler_node(state: ApplicationState) -> ApplicationState:
    print("[Node] FormFiller: Navigating ATS and filling inputs...")
    return state

def human_in_the_loop_node(state: ApplicationState) -> ApplicationState:
    print("[Node] HumanInTheLoop: Pausing for manual input...")
    # Handle 30-sec timeout logic
    return state

# --- 8. Logger (Db save & Post-Processing) ---
def logger_node(state: ApplicationState) -> ApplicationState:
    print("[Node] Logger: Saving results & Generating Interview Cheat-Sheet...")
    state["submission_status"] = "Applied" if not state.get("errors") else "Failed"
    return state
