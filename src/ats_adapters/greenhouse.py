"""
Greenhouse specific locators and Playwright automation logic.
"""
from src.ats_adapters.base import BaseATSAdapter
from src.state import ApplicationState, FieldInference
from src.nodes.agent_nodes import get_structured_llm
import os
import asyncio

class GreenhouseAdapter(BaseATSAdapter):
    async def apply(self, page, state: ApplicationState) -> ApplicationState:
        print("[GreenhouseAdapter] Beginning injection on Greenhouse DOM...")
        
        profile = state.get("candidate_profile", {})
        if not profile:
            raise ValueError("Candidate profile is missing from state!")

        # 1. Fill basic fields
        print("[GreenhouseAdapter] Filling Standard Fields...")
        full_name = profile.get("name", "Unknown")
        first_name = full_name.split()[0] if full_name else ""
        last_name = " ".join(full_name.split()[1:]) if " " in full_name else "Unknown"

        try:
            # Name
            await page.fill('input#first_name', first_name)
            await page.fill('input#last_name', last_name)
            
            # Contact
            if profile.get("email"):
                await page.fill('input#email', profile["email"])
            if profile.get("phone"):
                await page.fill('input#phone', profile["phone"])
            
            # Resume Upload (using static resume1.pdf for now)
            resume_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'resumes', 'resume1.pdf'))
            if os.path.exists(resume_path):
                print(f"[GreenhouseAdapter] Uploading Resume: {resume_path}")
                # Greenhouse usually hides the real input behind a button, so we target the file input directly
                file_input = page.locator('input[type="file"]').first
                await file_input.set_input_files(resume_path)
            
            # LinkedIn (Specific to Greenhouse custom field mapping)
            if profile.get("linkedin_url"):
                # Greenhouse often puts LinkedIn in the first custom string field
                linkedin_locator = page.locator('input[autocomplete="custom-question-linkedin-profile"]')
                if await linkedin_locator.count() > 0:
                    await linkedin_locator.fill(profile["linkedin_url"])
                else:
                    # Fallback: search for a label containing 'LinkedIn'
                    print("[GreenhouseAdapter] Exact LinkedIn locator not found, searching via label...")
            
        except Exception as e:
            print(f"[GreenhouseAdapter ERROR] Standard field mapping failed: {e}")
            state["errors"].append(f"Greenhouse field error: {str(e)}")

        # 2. Extract Custom Questions for Precedence Chain / HITL
        print("[GreenhouseAdapter] Scanning for Custom Questions...")
        custom_fields = page.locator('.custom_field, .custom_question, div[data-custom-field]')
        count = await custom_fields.count()
        
        found_questions = []
        for i in range(count):
            field = custom_fields.nth(i)
            # Find the label text describing the question
            label_locator = field.locator('label')
            if await label_locator.count() > 0:
                label_text = await label_locator.first.inner_text()
                clean_label = label_text.split('\n')[0].strip() # Remove the asterisk and extra lines
                
                if clean_label:
                    found_questions.append({"label": clean_label, "index": i})
                    
                    label_lower = clean_label.lower()
                    
                    # See if it's a dropdown/select or a text input
                    text_input = field.locator('input[type="text"], textarea')
                    select_input = field.locator('select')
                    
                    # 1. URL Fallbacks
                    if "linkedin" in label_lower and profile.get("linkedin_url"):
                        if await text_input.count() > 0:
                            await text_input.first.fill(profile["linkedin_url"])
                            print(f"[GreenhouseAdapter] Filled LinkedIn URL: {clean_label}")
                        continue
                    
                    if "github" in label_lower and profile.get("github_url"):
                        if await text_input.count() > 0:
                            await text_input.first.fill(profile["github_url"])
                            print(f"[GreenhouseAdapter] Filled GitHub URL: {clean_label}")
                        continue

                    if ("website" in label_lower or "portfolio" in label_lower):
                        url = profile.get("portfolio_url") or profile.get("github_url")
                        if url and await text_input.count() > 0:
                            await text_input.first.fill(url)
                            print(f"[GreenhouseAdapter] Filled Website URL: {clean_label}")
                        continue

                    # 2. Notice Period
                    if "notice" in label_lower and "period" in label_lower:
                        print(f"[GreenhouseAdapter] Handling Notice Period: {clean_label}")
                        if await select_input.count() > 0:
                            print(f"  [>] Select Dropdown found")
                        elif await text_input.count() > 0:
                            print(f"  [>] Text Input found")
                            if "day" in label_lower or "number" in label_lower or "numeric" in label_lower:
                                await text_input.first.fill("7 days")
                                print("  [>] Filled '7 days'")
                            else:
                                await text_input.first.fill("Immediate")
                                print("  [>] Filled 'Immediate'")
                        continue
                        
                    # 3. Handle Other Custom Situational Questions via LLM
                    print(f"[GreenhouseAdapter] Generating answer for custom question: '{clean_label}'")
                    llm = get_structured_llm(FieldInference)
                    from langchain_core.messages import SystemMessage, HumanMessage
                    
                    sys_msg = SystemMessage(content="You are an expert AI Job Application Assistant. Given a candidate profile and a form question, infer the absolute best short string answer to fill in the application box. Do not output anything other than the exact string to type. Be concise. If it requires a Yes/No, reply with exactly Yes or No.")
                    hum_msg_content = f"Candidate Profile: {profile}\n\nQuestion: {clean_label}"
                    
                    if await select_input.count() > 0:
                        options_text = await select_input.first.inner_text()
                        opts = [o.strip() for o in options_text.split('\n') if o.strip() and o.strip() != 'Please select']
                        hum_msg_content += f"\nOptions available: {opts}\nReturn EXACTLY one of the options."
                        
                    hum_msg = HumanMessage(content=hum_msg_content)
                    
                    try:
                        inference = llm.invoke([sys_msg, hum_msg])
                        ans = inference.inferred_answer
                        
                        if await select_input.count() > 0:
                            # Try to select the exact option text
                            try:
                                await select_input.first.select_option(label=ans)
                                print(f"  [>] Generated & Selected Dropdown: '{ans}' (Confidence: {inference.confidence})")
                            except Exception:
                                # Fallback
                                await select_input.first.select_option(index=1)
                                print("  [>] Fallback selected dropdown index=1")
                        elif await text_input.count() > 0:
                            await text_input.first.fill(str(ans))
                            print(f"  [>] Generated & Filled: '{ans}' (Confidence: {inference.confidence})")
                        else:
                            # E.g., radio buttons or checkboxes (advanced situational fallback)
                            # We write a naive try to find a label matching the answer and click its input
                            label_match = field.locator(f'label:has-text("{ans}")')
                            if await label_match.count() > 0:
                                await label_match.first.click()
                                print(f"  [>] Generated & Clicked Radio/Checkbox: '{ans}'")
                            else:
                                print(f"  [>] No suitable input field found to place answer: '{ans}'")
                    except Exception as llm_err:
                        print(f"  [>] Failed to invoke LLM for custom question: {llm_err}")
                                
        print(f"[GreenhouseAdapter] Found {len(found_questions)} custom questions.")
        state["form_fields_found"] = found_questions

        # 4. Final Submission
        print("[GreenhouseAdapter] Injection complete. Applying for the Job!")
        try:
            # We attempt to find the submit button
            submit_btn = page.locator('button#submit_app, input#submit_app, input[type="submit"], button[type="submit"], input[name="commit"]')
            if await submit_btn.count() > 0:
                await submit_btn.first.click()
                print("[GreenhouseAdapter] SUCCESS: Submit button clicked.")
                # Give it a tiny bit of time to start network request before closing/returning
                await asyncio.sleep(5)
            else:
                print("[GreenhouseAdapter] WARNING: Could not find 'submit_app' button.")
        except Exception as e:
            print(f"[GreenhouseAdapter ERROR] Could not click submit: {e}")
            state["errors"].append(f"Greenhouse submit error: {str(e)}")
        
        return state