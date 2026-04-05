from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class CandidateProfile(Base):
    __tablename__ = 'candidate_profiles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    linkedin_url = Column(String(255))
    github_url = Column(String(255))
    leetcode_url = Column(String(255))
    portfolio_url = Column(String(255))
    
    # JSON fields for flexible storage of parsed resume
    work_history = Column(JSON) # e.g. [{"company": "X", "title": "SE", "description": "..."}]
    education = Column(JSON)
    skills = Column(JSON)
    base_resume_text = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class CustomAnswer(Base):
    __tablename__ = 'custom_answers'
    
    id = Column(Integer, primary_key=True)
    question_keyword = Column(String(500), unique=True, index=True) # E.g., 'requires_sponsorship'
    answer = Column(Text, nullable=False)
    
class JobQueue(Base):
    __tablename__ = 'jobs_queue'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(2000), nullable=False)
    status = Column(String(50), default='Pending') # Pending, Tailoring, Navigating, Applied, Failed, Skipped
    ats_platform = Column(String(100))
    match_score = Column(Float)
    failure_reason = Column(Text)
    
    # Assets created for this specific application
    tailored_resume_text = Column(Text)
    cover_letter_text = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
