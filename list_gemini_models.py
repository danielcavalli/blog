#!/usr/bin/env python3
"""List available Gemini models and their supported methods."""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

for model in client.models.list():
    print(model.name)
    if hasattr(model, "supported_actions") and model.supported_actions:
        print(f"  methods: {', '.join(model.supported_actions)}")
    if hasattr(model, "description"):
        print(f"  description: {model.description}")
    print()
