import gitlab
import re
import time # Tambahkan import time
from config import settings

class GitLabService:
    def __init__(self):
        """Initializes the GitLab Service and connects to the server."""
        try:
            self.client = gitlab.Gitlab(
                settings.GITLAB_SERVER,
                private_token=settings.GITLAB_PRIVATE_TOKEN,
                ssl_verify=False
            )
            # self.client.auth()
            print("Successfully connected to GitLab (SSL verification disabled).")
        except gitlab.exceptions.GitlabAuthenticationError:
            print("GitLab authentication failed. Please check your token.")
            raise

    def get_merge_request_diff(self, mr_url):
        """
        Fetches the code diff from a GitLab Merge Request URL.
        Returns a string containing the diff.
        """
        project_path = self._parse_project_path_from_mr_url(mr_url)
        mr_iid = self._parse_mr_iid_from_url(mr_url)

        if not project_path or not mr_iid:
            print(f"Could not parse project path or MR IID from URL: {mr_url}")
            return None

        try:
            project = self.client.projects.get(project_path)
            mr = project.mergerequests.get(mr_iid)
            
            start_time = time.time()
            changes = mr.changes()['changes']
            end_time = time.time()
            print(f"Time taken to fetch MR changes from GitLab API: {end_time - start_time:.2f} seconds")

            diff_text = ""
            for change in changes:
                diff_text += f"--- a/{change['old_path']}\n"
                diff_text += f"+++ b/{change['new_path']}\n"
                diff_text += f"{change['diff']}\n"
            
            print(f"Successfully fetched diff for MR !{mr_iid} in project {project.path_with_namespace}")
            return diff_text
        except gitlab.exceptions.GitlabGetError as e:
            print(f"Error finding project or MR. Project: '{project_path}', MR: '!{mr_iid}'. Details: {e}")
            return None

    def get_commit_diff(self, commit_url):
        """
        Fetches the code diff from a GitLab Commit URL.
        Returns a string containing the diff.
        """
        project_path = self._parse_project_path_from_commit_url(commit_url)
        commit_sha = self._parse_commit_sha_from_url(commit_url)

        if not project_path or not commit_sha:
            print(f"Could not parse project path or commit SHA from URL: {commit_url}")
            return None

        try:
            project = self.client.projects.get(project_path)
            commit = project.commits.get(commit_sha)
            
            start_time = time.time()
            # Pass all=True to ensure we get all changes, not just the first page
            diffs = commit.diff(all=True)
            end_time = time.time()
            print(f"Time taken to fetch commit diff from GitLab API: {end_time - start_time:.2f} seconds. Files changed: {len(diffs)}")

            diff_text = ""
            for diff in diffs:
                diff_text += f"--- a/{diff['old_path']}\n"
                diff_text += f"+++ b/{diff['new_path']}\n"
                diff_text += f"{diff['diff']}\n"

            print(f"Successfully fetched diff for commit {commit.short_id} in project {project.path_with_namespace}")
            return diff_text
        except gitlab.exceptions.GitlabGetError as e:
            print(f"Error finding project or commit. Project: '{project_path}', Commit: '{commit_sha}'. Details: {e}")
            return None

    def _parse_project_path_from_mr_url(self, url):
        """Parses the project path from a GitLab Merge Request URL."""
        # This regex is designed to capture the full path including groups/subgroups
        match = re.search(r'https?://[^/]+/(.*?)/-/merge_requests/\d+', url)
        return match.group(1) if match else None

    def _parse_project_path_from_commit_url(self, url):
        """Parses the project path from a GitLab Commit URL."""
        # This regex is designed to capture the full path including groups/subgroups
        match = re.search(r'https?://[^/]+/(.*?)/commit/[a-f0-9]+', url)
        return match.group(1) if match else None

    def _parse_mr_iid_from_url(self, url):
        """Parses the Merge Request IID from a GitLab URL."""
        match = re.search(r'/merge_requests/(\d+)', url)
        return int(match.group(1)) if match else None

    def _parse_commit_sha_from_url(self, url):
        """Parses the Commit SHA from a GitLab URL."""
        # More flexible regex to find the commit SHA
        match = re.search(r'/commit/([a-f0-9]+)', url)
        return match.group(1) if match else None
