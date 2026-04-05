import asyncio
import os
import sys
from dotenv import load_dotenv


# Ensure the root directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langgraph.graph import StateGraph, END
from src.state import ApplicationState
from src.nodes.agent_nodes import (
    parse_resume_node,
    browser_scraper_node,
    triage_agent_node,
    asset_generator_node,
    human_in_the_loop_node,
    logger_node
)
from src.nodes.browser_automator import form_filler_node

# Load environment variables
load_dotenv()

def build_graph():
    # Define state tracking
    workflow = StateGraph(ApplicationState)
    
    # Add Nodes
    workflow.add_node("onboarding", parse_resume_node)
    workflow.add_node("scraper", browser_scraper_node)
    workflow.add_node("triage", triage_agent_node)
    workflow.add_node("asset_generator", asset_generator_node)
    workflow.add_node("browser_automator", form_filler_node) # Using combined form filler for simplicity
    workflow.add_node("human_fallback", human_in_the_loop_node)
    workflow.add_node("logger", logger_node)
    
    # Define execution order
    workflow.set_entry_point("onboarding")
    workflow.add_edge("onboarding", "scraper")
    workflow.add_edge("scraper", "triage")
    
    # Triage decision
    # If the score is > 60%, continue to generate assets. Else skip
    def should_continue(state: ApplicationState) -> str:
        if state.get("match_score", 0) >= 60.0:
            return "asset_generator"
        else:
            return "logger"
            
    workflow.add_conditional_edges("triage", should_continue)
    
    workflow.add_edge("asset_generator", "browser_automator")
    
    # browser_scraper is a regular coroutine since it uses async playwright
    # but the way we added it to langgraph might be swallowing the output or failing if it wasn't awaited right.
    # Actually wait, form_filler_node is async too.

    workflow.add_edge("browser_automator", "human_fallback")
    workflow.add_edge("human_fallback", "logger")
    workflow.add_edge("logger", END)
    
    compiled_graph = workflow.compile()
    
    return compiled_graph

async def run_pipeline():
    print("--- Starting AI Job Application Orchestrator ---")
    
    app_graph = build_graph()
    
    # Initialize the basic state for a new application process
    initial_state: ApplicationState = {
        "candidate_id": 1,
        "candidate_profile": {
            "name": "Suraj Sharma",
            "email": "sharmasuraj1b@gmail.com",
            "phone": "9576531113",
            "linkedin_url": "https://linkedin.com/in/surajsharma2901",
            "github_url": "https://github.com/SurajSharma2901"
        },
        "job_url": "https://job-boards.greenhouse.io/anchanto/jobs/7684881003?gh_src=my.greenhouse.search",
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
    
    # Run graph execution
    async for event in app_graph.astream(initial_state):
        node_name = list(event.keys())[0]
        state_data = list(event.values())[0]
        print(f"✅ Reached step: {node_name}")
        # print("State partial:", state_data.get("match_score", "..."), " | ", state_data.get("submission_status", "..."))
        
    print("--- Execution Complete ---")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
