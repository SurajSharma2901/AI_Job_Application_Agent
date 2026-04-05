import asyncio
from playwright.async_api import async_playwright
from src.state import ApplicationState
from src.ats_adapters.greenhouse import GreenhouseAdapter
import os

async def form_filler_node(state: ApplicationState) -> ApplicationState:
    print(f"[Node] FormFiller: Opening Playwright for {state['ats_platform']} ATS...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # For debugging locally, you can see it working!
        
        # You'd normally use stealth here
        context = await browser.new_context()
        page = await context.new_page()
        
        # Load the actual application page
        # In a real workflow, this comes from state["job_url"]
        # For testing, we'll try to reach it directly
        url_to_hit = state.get("job_url", "https://google.com")
        await page.goto(url_to_hit, timeout=60000)
        
        if state["ats_platform"] == "Greenhouse":
            print("[Node] FormFiller: Routing to Dedicated Greenhouse Adapter...")
            adapter = GreenhouseAdapter()
            state = await adapter.apply(page, state)
        else:
            print(f"[Node] FormFiller: No adapter found for {state['ats_platform']}. Falling back to Universal LLM Mapper.")
            # Universal LLM Logic Here
            pass

        # LLM inference simulation for custom questions in the HITL chain
        # The Custom Answer inference should happen on `state["form_fields_found"]`
        
        # Give us a few seconds to visually see the filled form before Playwright closes it down
        await asyncio.sleep(5)
        await browser.close()
        
    return state
