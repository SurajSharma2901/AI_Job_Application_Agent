from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ApplicationState(TypedDict):
    """State object for the LangGraph orchestrator."""
    candidate_id: int
    candidate_profile: Optional[Dict[str, Any]] # Will hold the structured JSON
    job_url: str
    
    # Scraped Data
    job_description: str
    ats_platform: str
    match_score: float
    
    # Tailored Assets
    tailored_resume_text: str
    cover_letter_text: str
    
    # Form Filling
    form_fields_found: List[Dict[str, Any]] # e.g. [{"name": "sponsorship", "required": True}]
    current_field_key: str
    
    # Final Result
    submission_status: str # "Applied", "Failed", "Skipped", "Manual"
    errors: List[str]
    
# Pydantic Schemas for Structured Outputs
class ParsedCandidate(BaseModel):
    name: str = Field(description="Full Name")
    email: str = Field(description="Email Address")
    phone: Optional[str] = Field(None, description="Phone Number")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn Profile URL")
    github_url: Optional[str] = Field(None, description="GitHub Profile URL")
    leetcode_url: Optional[str] = Field(None, description="LeetCode Profile URL")
    portfolio_url: Optional[str] = Field(None, description="Personal Website/Portfolio URL")
    work_history: List[Dict[str, Any]] = Field(description="List of roles, companies, dates, and descriptions")
    education: List[Dict[str, Any]] = Field(description="List of degrees, schools, and dates")
    skills: List[str] = Field(description="Core competencies extracted")
    projects: List[Dict[str, Any]] = Field(default_factory=list, description="List of projects with name, tech_stack (can be string or list), and description")
    certifications: List[str] = Field(default_factory=list, description="List of certifications or courses")

class TriageScore(BaseModel):
    score: float = Field(description="Match score between 0.0 and 100.0")
    reasoning: str = Field(description="Short rationale for the given score")

class TailoredAssets(BaseModel):
    tailored_resume_text: str = Field(description="Bullets rewritten to align with JD")
    cover_letter_text: str = Field(description="Professional, concise cover letter")

class FieldInference(BaseModel):
    inferred_answer: str = Field(description="The final string answer to fill in the form field")
    confidence: float = Field(description="Model confidence from 0.0 to 1.0 on this answer")
