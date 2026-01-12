import openai
import json
import re
import os
import certifi
from config import settings
import google.generativeai as genai

class AIService:
    def __init__(self):
        """Initializes the AI Service with the configured provider (Gemini or OpenAI)."""
        self.provider = settings.AI_SERVICE_PROVIDER
        self.client = None
        self.model_name = None
        self.api_key = None

        if self.provider == "gemini":
            self.api_key = settings.GEMINI_API_KEY
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is not set for Gemini provider.")
            genai.configure(api_key=self.api_key)
            self.model_name = 'gemini-2.5-pro'
            self.client = genai.GenerativeModel(self.model_name)
            print(f"AIService initialized with Google Gemini ({self.model_name}).")
        elif self.provider == "openai":
            self.api_key = settings.OPENAI_API_KEY
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is not set for OpenAI provider.")
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=settings.OPENAI_BASE_URL
            )
            self.model_name = "gpt-4o-mini"
            print("AIService initialized with OpenAI.")
        else:
            raise ValueError(f"Unsupported AI_SERVICE_PROVIDER: {self.provider}. Must be 'gemini' or 'openai'.")
        
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self):
        """Loads the prompt template from the file."""
        try:
            with open("prompts/code_review_prompt.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print("Error: prompts/code_review_prompt.txt not found.")
            raise

    def _clean_json_response(self, text):
        """Cleans the text to extract a valid JSON object."""
        # This regex is more robust and handles cases where the JSON is not perfectly formatted.
        # It looks for a string that starts with { and ends with }, and is greedy.
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        return text

    def _call_gemini_api(self, prompt):
        """Makes a call to the Gemini API using the official Google SDK."""
        # The response_mime_type can be set via generation_config
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        response = self.client.generate_content(prompt, generation_config=generation_config)
        return response.text

    def analyze_code_diff(self, code_diff):
        """
        Sends the code diff to the configured AI model for analysis and returns the structured result.
        """
        if not code_diff:
            print("Code diff is empty. Skipping analysis.")
            return None

        full_prompt = self.prompt_template.replace("{code_diff}", code_diff)
        
        print(f"Sending code diff to {self.provider} ({self.model_name}) for analysis...")
        try:
            response_text = None
            if self.provider == "gemini":
                response_text = self._call_gemini_api(full_prompt)
            elif self.provider == "openai":
                chat_completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": full_prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                response_text = chat_completion.choices[0].message.content

            if response_text:
                cleaned_response = self._clean_json_response(response_text)
                print(f"Received analysis from {self.provider}.")
                return json.loads(cleaned_response)
            else:
                print(f"No response text received from {self.provider}.")
                return None

        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON from {self.provider} response: {e}. Raw response: {response_text}")
            return None
        except Exception as e:
            print(f"An error occurred with the {self.provider} API: {e}")
            return None