import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Jira Configuration
JIRA_SERVER = os.getenv("JIRA_SERVER")
JIRA_PAT = os.getenv("JIRA_PAT")

# GitLab Configuration
GITLAB_SERVER = os.getenv("GITLAB_SERVER")
GITLAB_PRIVATE_TOKEN = os.getenv("GITLAB_PRIVATE_TOKEN")

# AI Model Configuration
AI_SERVICE_PROVIDER = os.getenv("AI_SERVICE_PROVIDER", "openai") # Default to 'openai'
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# Local Git Repository Path for cloning
LOCAL_GIT_REPO_PATH = os.getenv("LOCAL_GIT_REPO_PATH", "temp_repos")

# --- NEW ---
# Workflow Configuration
# Controls whether to automatically transition a ticket when AI recommends 'Revisi'
AUTO_TRANSITION_REVISI = os.getenv("AUTO_TRANSITION_REVISI", "false").lower() == "true"


def validate_config():
    """Validates that all necessary configuration variables are set."""
    required_vars = {
        "JIRA_SERVER": JIRA_SERVER,
        "JIRA_PAT": JIRA_PAT,
        "GITLAB_SERVER": GITLAB_SERVER,
        "GITLAB_PRIVATE_TOKEN": GITLAB_PRIVATE_TOKEN,
        "AI_SERVICE_PROVIDER": AI_SERVICE_PROVIDER,
        "LOCAL_GIT_REPO_PATH": LOCAL_GIT_REPO_PATH,
    }

    if AI_SERVICE_PROVIDER == "gemini":
        required_vars["GEMINI_API_KEY"] = GEMINI_API_KEY
    elif AI_SERVICE_PROVIDER == "openai":
        required_vars["OPENAI_API_KEY"] = OPENAI_API_KEY
        # Base URL is optional, so we don't validate it
    else:
        raise ValueError(f"Unsupported AI_SERVICE_PROVIDER: {AI_SERVICE_PROVIDER}. Must be 'gemini' or 'openai'.")

    missing_vars = [key for key, value in required_vars.items() if value is None]

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    print("Configuration loaded and validated successfully.")
