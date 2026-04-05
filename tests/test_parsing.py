import asyncio
import os
import sys
from dotenv import load_dotenv
import PyPDF2

# Ensure the root directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.prompts import PromptTemplate
from src.state import ParsedCandidate

load_dotenv()

def extract_text_from_pdf(pdf_path: str) -> str:
    print(f"Extracting text from: {pdf_path}")
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

async def test_resume_parsing():
    resumes_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'resumes')
    pdf_path = os.path.join(resumes_dir, 'resume1.pdf')
    
    if not os.path.exists(pdf_path):
        print(f"Resume not found at: {pdf_path}")
        return

    # 1. Extract text from PDF
    raw_resume_text = extract_text_from_pdf(pdf_path)
    
    if not raw_resume_text.strip():
        print("Failed to extract text from the PDF. It might be empty or scanned as an image.")
        return
    
    print(f"\n--- Extracted Text Preview (First 500 chars) ---\n{raw_resume_text[:500]}...\n--------------------------------------------------\n")
    
    # 2. Parse using LLM
    print("Calling LLM model to parse the resume structure (Attempting Gemini, fallback to Groq)...")
    from src.nodes.agent_nodes import get_structured_llm
    llm = get_structured_llm(ParsedCandidate)
    
    RESUME_PARSE_PROMPT = """
You are an expert technical recruiter and resume parser.

Your task is to extract structured information from the raw resume text provided below.
Be precise, do not infer or fabricate details that are not explicitly stated.
If a field is missing or unclear, leave it as null.

## Resume Text:
{raw_resume}

## Instructions:
Extract the following details:
- Full name
- Contact information (email, phone, LinkedIn, GitHub, LeetCode, Portfolio)
- Education (degree, institution, year, GPA if mentioned)
- Work experience (company, role, duration, key responsibilities)
- Skills (technical and soft skills, grouped if possible)
- Projects (name, tech stack, description, links if any)
- Certifications or courses
- Interests or extracurriculars (if mentioned)

Return a clean, structured output strictly matching the required schema.
Do NOT include any explanation, preamble, or markdown — only the structured data.
"""
    
    prompt = PromptTemplate.from_template(RESUME_PARSE_PROMPT)

    try:
        result = await llm.ainvoke(prompt.format(raw_resume=raw_resume_text[:10000])) # pass up to 10k chars
        print("\n✅ Parsing Successful!")
        print(f"Name: {result.name}")
        print(f"Email: {result.email}")
        print(f"Phone: {result.phone}")
        print(f"LinkedIn: {result.linkedin_url}")
        print(f"GitHub: {result.github_url}")
        print(f"Skills found: {len(result.skills)}")
        print(f"Jobs found: {len(result.work_history)}")
        print(f"Education found: {len(result.education)}")
        
        print("\n--- Full Parsed JSON ---")
        print(result.model_dump_json(indent=2))
        
    except Exception as e:
        print(f"\n❌ Parsing Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_resume_parsing())
