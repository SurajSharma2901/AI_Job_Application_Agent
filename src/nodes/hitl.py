import asyncio
from src.state import ApplicationState

async def _ask_user_input(field_name: str) -> str:
    print(f"\n⚠️ Action Required! The Form Filler encountered a low-confidence or sensitive field: '{field_name}'")
    print(f"Please provide the answer below within 30 seconds.")
    # Async input handling
    loop = asyncio.get_event_loop()
    # Use run_in_executor to avoid blocking the event loop with input()
    answer = await loop.run_in_executor(None, input, "Your Answer: ")
    return answer
    
async def human_in_the_loop_node(state: ApplicationState) -> ApplicationState:
    print(f"[Node] HumanInTheLoop: Pausing for manual input... Countdown Started (30s)")
    
    unanswered_fields = state.get("errors", [])
    if not unanswered_fields:
        print("[Node] HumanInTheLoop: No errors or unknown fields found. Proceeding.")
        return state
        
    for field in unanswered_fields:
        try:
            # Enforce the strict 30 second timeout on Human Input
            answer = await asyncio.wait_for(_ask_user_input(field), timeout=30.0)
            print(f"Received human answer: '{answer}'. Injecting back into ATS/DB...")
            
            # NOTE: In a complete implementation, this answer triggers a Self-Healing UPSERT 
            # operation back to Postgres (CustomAnswers table) right here.
            
            # Upsert into PostgreSQL pseudo-code:
            # session.merge(CustomAnswer(question_keyword=field, answer=answer))
            # session.commit()
            
        except asyncio.TimeoutError:
            print(f"\n[TIMEOUT] 30 seconds elapsed for field '{field}'. No human response. Skipping job application.")
            state["submission_status"] = "Skipped"
            break

    return state
