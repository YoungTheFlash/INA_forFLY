"""
Headless research harness for INA — runs the CORE pipeline without the GUI.

It exercises the real INA code path:
    screenshot (a file) + intention  ->  build prompt  ->  call LLM  ->  {output, reason, message}

No menu bar, no screen-recording permission, no AppleScript. Just the part you
will modify (prompt building) and evaluate (the generated nudge).

Usage:
    export OPENAI_API_KEY="sk-..."          # or GEMINI_API_KEY
    ./.venv/bin/python research_harness.py "Write my thesis" "/path/to/screenshot.png"

If you omit the arguments it uses a default intention and one of the sample
screenshots in the parent folder.
"""

import os
import sys
import json

# --- inputs ---------------------------------------------------------------
DEFAULT_INTENTION = "Write my thesis"
DEFAULT_IMAGE = os.path.join(
    os.path.dirname(__file__), "..", "截屏2026-06-14 14.06.27.png"
)

intention = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INTENTION
image_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_IMAGE

# Pretend the frontmost app is a browser on a distracting page (you can edit this).
frontmost_app = {"app_name": "Google Chrome", "url": "youtube.com/watch?v=highlights"}

# --- build the prompt (the part you will modify for personalization) -------
from src.config.prompt_config import PromptConfig

prompt = PromptConfig(storage=None).get_advanced_prompt(
    task_name=intention,
    frontmost_app=frontmost_app,
)
print("=" * 60)
print(f"Intention : {intention}")
print(f"Screenshot: {image_path}")
print(f"Prompt built: {len(prompt)} chars")
print("=" * 60)

# --- call the LLM (the same client the app uses) ---------------------------
from src.utils.direct_llm_client import get_configured_client

client = get_configured_client()
if not client:
    print("\n[NO API KEY] Prompt was built successfully, but no LLM was called.")
    print("Set a key first, e.g.:  export OPENAI_API_KEY=\"sk-...\"")
    sys.exit(0)

with open(image_path, "rb") as f:
    image_bytes = f.read()

context = {
    "current_task": intention,
    "frontmost_app": frontmost_app,
    "session_id": "research_harness",
    "user_id": "researcher",
}

result = client.analyze_screen(image_data=image_bytes, prompt=prompt, context=context)

print("\n----- LLM RESULT -----")
print(f"distraction score (output): {result.get('output')}")
print(f"reason : {result.get('reason')}")
print(f"nudge  (message): {result.get('message')}")
print("\nfull JSON:")
print(json.dumps({k: v for k, v in result.items() if k != 'prompt'},
                 ensure_ascii=False, indent=2))
