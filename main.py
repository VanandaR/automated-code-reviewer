import argparse
import sys
from urllib.parse import urlparse
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress only the InsecureRequestWarning from urllib3 needed for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import re
from config import settings
from services.jira_service import JiraService
from services.gitlab_service import GitLabService
from services.ai_service import AIService
from services.git_service import GitService

def extract_mr_url(text):
    """Extracts the first GitLab Merge Request URL from a given text."""
    # Simplified, more robust regex to find MR URLs inside Jira's link format.
    # This pattern is more flexible:
    # - It can handle an optional "mr:" prefix.
    # - It handles both "/-/merge_requests/" and "/merge_requests/".
    # - It captures the URL correctly whether it's in Jira's link format or plain text.
    pattern = r"\[?(https?://[^\]|]+(?:/-)?/merge_requests/\d+)"
    match = re.search(pattern, text)
    return match.group(1) if match else None

def extract_commit_url(text):
    """Extracts the first GitLab Commit URL from a given text."""
    # Simplified, more robust regex to find commit URLs inside Jira's link format.
    pattern = r"\[?(https?://[^\]|]+/commit/[a-f0-9]+)"
    match = re.search(pattern, text)
    return match.group(1) if match else None

def format_analysis_category(category_name, findings):
    """Helper function to format a single category of findings."""
    if not findings:
        return ""
    
    section = f"h3. {category_name}\n"
    for finding in findings:
        file_info = finding.get('file', 'N/A')
        line_info = finding.get('line')
        location = f"`{file_info}:{line_info}`" if line_info else f"`{file_info}`"
        
        section += f"* {finding.get('comment', 'No comment provided.')} ({location})\n"
    return section + "\n"

def format_comment(analysis_result, url, assignee_name):
    """Formats the detailed analysis result into a Jira comment."""
    if not analysis_result:
        return "Analisis AI tidak menghasilkan temuan yang valid."

    # Determine link type (MR or Commit)
    link_type = "Commit" if "/commit/" in url else "Merge Request"

    # Main header and link
    comment = f"h2. 🤖 Hasil Code Review\n"
    comment += f"*{link_type}*: [{url}|{url}]\n\n"
    
    # Change Summary
    comment += f"h3. Ringkasan Perubahan\n"
    comment += f"{analysis_result.get('change_summary', 'Tidak ada ringkasan perubahan.')}\n\n"
    
    # Detailed Analysis
    analysis = analysis_result.get('analysis', {})
    
    # Format "Perubahan Diperlukan"
    perubahan_diperlukan = analysis.get("perubahan_diperlukan", [])
    if perubahan_diperlukan:
        comment += f"h3. ⚠️ Perubahan Diperlukan\n"
        for finding in perubahan_diperlukan:
            file_info = finding.get('file', 'N/A')
            line_info = finding.get('line')
            location = f"`{file_info}:{line_info}`" if line_info else f"`{file_info}`"
            comment += f"* {finding.get('comment', 'No comment provided.')} ({location})\n"
            if 'rekomendasi' in finding:
                comment += f"{{code}}\n{finding['rekomendasi']}\n{{code}}\n"
        comment += "\n"

    # Format "Sudah Baik"
    sudah_baik = analysis.get("sudah_baik", [])
    if sudah_baik:
        comment += f"h3. ✅ Sudah Baik\n"
        for finding in sudah_baik:
            file_info = finding.get('file', 'N/A')
            line_info = finding.get('line')
            location = f"`{file_info}:{line_info}`" if line_info else f"`{file_info}`"
            comment += f"* {finding.get('comment', 'No comment provided.')} ({location})\n"
        comment += "\n"
    
    # Conclusion
    comment += f"h3. Kesimpulan\n"
    comment += f"{analysis_result.get('conclusion', 'Tidak ada kesimpulan.')}\n"
    
    return comment

def main_workflow(ticket_id):
    """The main workflow of the application."""
    print("--- STEP 1: Initializing services... ---")
    jira_service = JiraService()
    gitlab_service = GitLabService()
    ai_service = AIService()
    git_service = GitService() # Initialize GitService
    
    # Initialize DiffFetcher with both gitlab_service and git_service
    diff_fetcher = DiffFetcher(gitlab_service, git_service)
    print("--- STEP 1 COMPLETE ---")

    print(f"\n--- STEP 2: Fetching details for ticket {ticket_id}... ---")
    issue = jira_service.get_ticket_details(ticket_id)
    if not issue:
        print("--- EXIT: Failed to fetch issue. ---")
        return
    print("--- STEP 2 COMPLETE ---")

    assignee = issue.fields.assignee
    if not assignee:
        print("--- EXIT: Ticket is not assigned. ---")
        return
        
    assignee_name = assignee.name

    print("\n--- STEP 3: Searching for GitLab URL (MR or Commit)... ---")
    
    # Create a list of texts to search: description first, then all comments
    texts_to_search = [issue.fields.description or ""]
    if hasattr(issue.fields, 'comment') and issue.fields.comment.comments:
        texts_to_search.extend([comment.body for comment in issue.fields.comment.comments])

    # Collect all URLs found, we'll use the LAST one
    all_urls = []
    for text in texts_to_search:
        # Find all MR URLs in this text
        mr_url = extract_mr_url(text)
        if mr_url:
            all_urls.append((mr_url, "MR"))
        
        # Find all Commit URLs in this text
        commit_url = extract_commit_url(text)
        if commit_url:
            all_urls.append((commit_url, "Commit"))

    gitlab_url = None
    url_type = None
    
    if all_urls:
        # Take the LAST URL found
        gitlab_url, url_type = all_urls[-1]
        print(f"   Found {len(all_urls)} URL(s), using last one:")
        print(f"   {url_type} URL: {gitlab_url}")

    if not gitlab_url:
        print("--- EXIT: No GitLab URL found. ---")
        return
    print("--- STEP 3 COMPLETE ---")

    print("\n--- STEP 4: Fetching code diff from GitLab... ---")
    code_diff = None
    if url_type == "MR":
        # For MRs, we still rely on GitLab API as local git doesn't have direct MR concept
        code_diff = diff_fetcher.fetch_gitlab_mr_diff(gitlab_url)
    elif url_type == "Commit":
        # For Commits, DiffFetcher will decide between local Git or GitLab API
        code_diff = diff_fetcher.fetch_commit_diff(gitlab_url)

    if not code_diff:
        print("--- EXIT: Failed to fetch code diff. ---")
        return
    print("--- STEP 4 COMPLETE ---")

    print("\n--- STEP 5: Analyzing code diff with AI... ---")
    analysis_result = ai_service.analyze_code_diff(code_diff)
    if not analysis_result:
        print("--- EXIT: AI analysis failed or returned no result. ---")
        return
    print("--- STEP 5 COMPLETE ---")

    print("\n--- STEP 6: Formatting comment for Jira... ---")
    jira_comment = format_comment(analysis_result, gitlab_url, assignee_name)
    print("--- STEP 6 COMPLETE ---")
    
    print("\n--- STEP 7: Posting comment to Jira ticket... ---")
    jira_service.post_comment(ticket_id, jira_comment)
    print("--- STEP 7 COMPLETE ---")
    
    # --- STEP 8: Transition Jira ticket and handle cloned issue ---
    print("\n--- STEP 8: Transitioning Jira ticket based on AI conclusion... ---")
    conclusion = analysis_result.get('conclusion', '').strip().lower()
    
    transition_successful = False
    if 'staging' in conclusion:
        print("   AI conclusion contains 'Staging'. Attempting to transition ticket...")
        jira_service.transition_ticket_status(ticket_id, "➔ Staging")
    elif 'revisi' in conclusion:
        if settings.AUTO_TRANSITION_REVISI:
            print("   AI conclusion contains 'Revisi' and AUTO_TRANSITION_REVISE is enabled. Attempting to transition ticket...")
            transition_successful = jira_service.transition_ticket_status(ticket_id, "➔ Revisi")
            if transition_successful:
                print("   Transition to 'Revisi' successful. Looking for the cloned ticket...")
                # Give Jira a moment to create the clone and the link
                import time
                time.sleep(10) # 10-second delay
                
                cloned_issue = jira_service.find_cloned_issue(ticket_id)
                if cloned_issue:
                    print(f"   Found cloned ticket: {cloned_issue.key}. Appending analysis to its description.")
                    jira_service.update_issue_description(cloned_issue.key, jira_comment)
                else:
                    print("   Could not find a cloned ticket.")
        else:
            print("   AI conclusion contains 'Revisi', but AUTO_TRANSITION_REVISE is disabled. Skipping transition.")
    else:
        print("   No specific transition keyword ('Staging' or 'Revisi') found in AI conclusion.")
    print("--- STEP 8 COMPLETE ---")


def main():
    """Main function to run the AI System Analyst Assistant."""
    parser = argparse.ArgumentParser(
        description="AI System Analyst Assistant for automated code reviews."
    )
    parser.add_argument(
        "--ticket",
        type=str,
        help="One or more Jira ticket IDs to analyze, separated by commas (e.g., 'PROJ-123,PROJ-124')."
    )
    parser.add_argument(
        "--local-repo-path",
        type=str,
        help="Path to a local Git repository to analyze. If provided, --ticket is optional."
    )
    parser.add_argument(
        "--commit-sha",
        type=str,
        help="Commit SHA to analyze in the local repository. Required if --local-repo-path is provided."
    )
    parser.add_argument(
        "--ai-provider",
        type=str,
        default=settings.AI_SERVICE_PROVIDER,
        choices=["gemini", "openai"],
        help="The AI service provider to use (e.g., 'gemini', 'openai'). Defaults to settings.AI_SERVICE_PROVIDER."
    )

    args = parser.parse_args()
    # Accept comma-separated tickets and split them into a list
    ticket_ids_str = args.ticket
    ticket_id = ticket_ids_str.split(',') if ticket_ids_str else None
    local_repo_path = args.local_repo_path
    commit_sha = args.commit_sha
    ai_provider = args.ai_provider

    if not ticket_id and not local_repo_path:
        parser.error("Either --ticket or --local-repo-path must be provided.")
    if local_repo_path and not commit_sha:
        parser.error("--commit-sha is required when --local-repo-path is provided.")

    # Override the AI service provider from settings if specified in CLI
    settings.AI_SERVICE_PROVIDER = ai_provider

    # Since ticket_id is now a list, we handle it differently
    if ticket_id:
        print(f"--- Starting analysis for Jira tickets: {', '.join(ticket_id)} using {settings.AI_SERVICE_PROVIDER} ---")
    elif local_repo_path:
        print(f"--- Starting analysis for local repository: {local_repo_path} (Commit: {commit_sha}) using {settings.AI_SERVICE_PROVIDER} ---")

    try:
        settings.validate_config()
        if local_repo_path and commit_sha:
            local_workflow(local_repo_path, commit_sha)
        elif ticket_id:
            # Loop through each ticket ID provided
            for single_ticket_id in ticket_id:
                try:
                    print(f"\n\n--- Processing ticket: {single_ticket_id} ---")
                    main_workflow(single_ticket_id)
                    print(f"--- Successfully completed analysis for ticket: {single_ticket_id} ---")
                except Exception as e:
                    # Log the error for the specific ticket and continue with the next one
                    print(f"\n--- An error occurred while processing ticket {single_ticket_id}: {e} ---", file=sys.stderr)
                    # Optionally, continue to the next ticket instead of exiting
                    continue
    except (ValueError, Exception) as e:
        # This will catch initialization errors, e.g., config validation
        print(f"\nAn error occurred during initial setup: {e}", file=sys.stderr)
        sys.exit(1)

    if ticket_id:
        print(f"\n\n--- All ticket processing completed. ---")
    elif local_repo_path:
        print(f"\n--- Analysis for local repository {local_repo_path} completed successfully. ---")

def local_workflow(repo_path, commit_sha):
    """Workflow for analyzing a local Git repository."""
    print("--- STEP 1: Initializing services... ---")
    # JiraService and AIService might still be needed for posting comments later or just AI analysis
    gitlab_service = GitLabService() # Still needed for DiffFetcher
    git_service = GitService()
    ai_service = AIService()
    
    diff_fetcher = DiffFetcher(gitlab_service, git_service)
    print("--- STEP 1 COMPLETE ---")

    print(f"\n--- STEP 2: Fetching code diff from local repository {repo_path} for commit {commit_sha}... ---")
    code_diff = diff_fetcher.fetch_local_repo_diff(repo_path, commit_sha)

    if not code_diff:
        print("--- EXIT: Failed to fetch code diff from local repository. ---")
        return
    print("--- STEP 2 COMPLETE ---")

    print("\n--- STEP 3: Analyzing code diff with AI... ---")
    analysis_result = ai_service.analyze_code_diff(code_diff)
    if not analysis_result:
        print("--- EXIT: AI analysis failed or returned no result. ---")
        return
    print("--- STEP 3 COMPLETE ---")

    print("\n--- STEP 4: Formatting analysis result... ---")
    # For local analysis, we don't have a Jira assignee or a GitLab URL directly.
    # We might need to adjust format_comment or create a new formatting function
    # For now, let's just print the analysis result.
    # In a real scenario, you might want to output this to a file or a dedicated report.
    formatted_analysis = format_comment(analysis_result, f"Local Repo: {repo_path} (Commit: {commit_sha})", "N/A")
    print("\n--- AI Analysis Result ---")
    print(formatted_analysis)
    print("--- STEP 4 COMPLETE ---")


class DiffFetcher:
    def __init__(self, gitlab_service: GitLabService, git_service: GitService):
        self.gitlab_service = gitlab_service
        self.git_service = git_service

    def fetch_commit_diff(self, commit_url):
        print(f"Attempting to fetch diff for commit via GitLab API: {commit_url}")
        return self.gitlab_service.get_commit_diff(commit_url)

    def fetch_gitlab_mr_diff(self, mr_url):
        # MR diffs currently only supported via GitLab API
        return self.gitlab_service.get_merge_request_diff(mr_url)

    def fetch_local_repo_diff(self, repo_path, commit_sha):
        """
        Fetches the diff for a specific commit directly from a local repository path.
        """
        print(f"Fetching diff for commit {commit_sha} from local repository: {repo_path}")
        # When analyzing a local repo provided by path, we might not want to fetch from remote origin by default,
        # or we should allow it to fail gracefully if no remote is configured.
        # Passing fetch_remote=True (default in new GitService method) but relying on the warning logic there.
        return self.git_service.get_commit_diff(repo_path, commit_sha, fetch_remote=True)

if __name__ == "__main__":
    main()