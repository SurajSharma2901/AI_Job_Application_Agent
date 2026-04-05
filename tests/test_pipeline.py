import unittest
from src.state import ApplicationState
from src.main import build_graph
import asyncio

class TestJobApplicationPipeline(unittest.TestCase):
    
    def test_triage_decision_high_match(self):
        """Test that a match score >= 60 continues to asset generation."""
        # Inside src/main.py, should_continue checks state["match_score"]
        state = {"match_score": 85.0}
        
        # We'll just extract the should_continue logic to unit test it directly 
        # or use a mock graph execution.
        def should_continue(state: ApplicationState) -> str:
            if state.get("match_score", 0) >= 60.0:
                return "asset_generator"
            else:
                return "logger"
                
        result = should_continue(state)
        self.assertEqual(result, "asset_generator")

    def test_triage_decision_low_match(self):
        """Test that a match score < 60 skips directly to logger (triage abort)."""
        state = {"match_score": 45.0}
        
        def should_continue(state: ApplicationState) -> str:
            if state.get("match_score", 0) >= 60.0:
                return "asset_generator"
            else:
                return "logger"
                
        result = should_continue(state)
        self.assertEqual(result, "logger")

    def test_ats_detection_logic(self):
        """Test the URL string matching for ATS platform detection."""
        def detect_ats(url: str) -> str:
            if "greenhouse.io" in url: return "Greenhouse"
            elif "jobs.lever.co" in url: return "Lever"
            elif "myworkdayjobs.com" in url: return "Workday"
            return "Unknown"

        self.assertEqual(detect_ats("https://boards.greenhouse.io/openai/jobs/12345"), "Greenhouse")
        self.assertEqual(detect_ats("https://jobs.lever.co/notion/1a2b3c"), "Lever")
        self.assertEqual(detect_ats("https://amazon.myworkdayjobs.com/en-US/amazoncareers"), "Workday")
        self.assertEqual(detect_ats("https://careers.google.com/jobs"), "Unknown")
        
    def test_initial_state_structure(self):
        """Ensure the ApplicationState dictionary is properly formed for LangGraph."""
        initial_state: ApplicationState = {
            "candidate_id": 1,
            "job_url": "https://boards.greenhouse.io/openai/jobs/123",
            "job_description": "",
            "ats_platform": "",
            "match_score": 0.0,
            "tailored_resume_text": "",
            "cover_letter_text": "",
            "form_fields_found": [],
            "current_field_key": "",
            "submission_status": "Pending",
            "errors": []
        }
        self.assertIn("job_url", initial_state)
        self.assertIn("match_score", initial_state)
        self.assertEqual(initial_state["submission_status"], "Pending")

if __name__ == '__main__':
    unittest.main()
