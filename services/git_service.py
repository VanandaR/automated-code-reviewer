import os
import subprocess
import shutil
import re
from urllib.parse import urlparse
from config import settings

class GitService:
    def __init__(self):
        """Initializes the Git Service."""
        self.temp_repo_dir = settings.LOCAL_GIT_REPO_PATH # From settings, e.g., 'temp_repos'
        os.makedirs(self.temp_repo_dir, exist_ok=True)
        print(f"GitService initialized. Temporary repository directory: {self.temp_repo_dir}")

    def _execute_git_command(self, command, cwd=None):
        """Executes a git command and returns its output."""
        try:
            full_command = ["git"] + command
            print(f"Executing Git command: {' '.join(full_command)}")
            result = subprocess.run(
                full_command,
                cwd=cwd if cwd else self.temp_repo_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {' '.join(full_command)}\nError: {e.stderr}")
            return None
        except FileNotFoundError:
            print("Git executable not found. Please ensure Git is installed and in your PATH.")
            return None

    def _get_repo_name_from_url(self, repo_url):
        """Extracts the repository name from a GitLab URL."""
        path = urlparse(repo_url).path
        # Remove leading '/rest-api/' if present, then split by '/'
        path_segments = [s for s in path.replace('/rest-api/', '/').split('/') if s]
        
        # The repository name is typically the last segment before '/-/merge_requests' or '/commit'
        # or the last segment if it's a direct repo URL.
        if '-/merge_requests' in path:
            # For MR URLs, the project path is before '-/merge_requests'
            match = re.search(r'/(.*?)/-/merge_requests', path)
            if match:
                project_path = match.group(1)
                return project_path.split('/')[-1] # Get the last part of the path
        elif '/commit/' in path:
            # For Commit URLs, the project path is before '/commit/'
            match = re.search(r'/(.*?)/commit/', path)
            if match:
                project_path = match.group(1)
                return project_path.split('/')[-1] # Get the last part of the path
        else:
            # General case for repository URL (e.g., https://gitlab.com/group/subgroup/project.git)
            # Remove '.git' suffix if present, and take the last segment
            repo_name = path_segments[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            return repo_name
        return None

    def clone_repository(self, repo_url, force_clone=False):
        """
        Clones a repository into a temporary directory.
        If the directory already exists, it will pull the latest changes
        unless force_clone is True, in which case it will re-clone.
        """
        repo_name = self._get_repo_name_from_url(repo_url)
        if not repo_name:
            print(f"Could not determine repository name from URL: {repo_url}")
            return None

        repo_path = os.path.join(self.temp_repo_dir, repo_name)

        if os.path.exists(repo_path):
            if force_clone:
                print(f"Force cloning: Removing existing repository at {repo_path}")
                shutil.rmtree(repo_path)
            else:
                print(f"Repository already exists at {repo_path}. Fetching latest changes.")
                if self._execute_git_command(["pull"], cwd=repo_path):
                    print(f"Successfully pulled latest changes for {repo_name}.")
                    return repo_path
                else:
                    print(f"Failed to pull latest changes for {repo_name}.")
                    return None
        
        print(f"Cloning {repo_url} into {repo_path}...")
        # Use a generic clone URL if the input is a commit/MR URL
        # Assuming the base URL for cloning can be derived
        # For simplicity, for now, we assume repo_url is clonable directly or we need a specific pattern
        
        # A more robust approach might extract the base project URL
        # For GitLab, it often looks like https://gitlab.customs.go.id/group/project.git
        # If the input URL is https://gitlab.customs.go.id/rest-api/smart-pcc-perencanaan/commit/...,
        # we need to construct the clonable URL.
        
        # Attempt to construct a clonable URL
        parsed_url = urlparse(repo_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Regex to find the project path from the URL
        project_path_match = re.search(r'https?://[^/]+/(.*?)(?:\.git)?(?:/-\/merge_requests|\/commit\/|$)', repo_url)
        if project_path_match:
            project_path = project_path_match.group(1)
            clone_url = f"{base_url}/{project_path}.git"
        else:
            print(f"Warning: Could not reliably extract clone URL from {repo_url}. Attempting to clone original URL.")
            # Ensure we don't double-add .git if it's already present
            clone_url = repo_url if repo_url.endswith('.git') else f"{repo_url}.git"

        if self._execute_git_command(["clone", clone_url, repo_path], cwd=self.temp_repo_dir):
            print(f"Successfully cloned {repo_name}.")
            return repo_path
        else:
            print(f"Failed to clone {repo_name}.")
            return None

    def get_commit_diff(self, repo_path, commit_sha, fetch_remote=True):
        """
        Fetches the diff for a specific commit in a locally cloned repository.
        Returns the diff as a string.
        If fetch_remote is True, it will first attempt to fetch from the remote 'origin'.
        """
        if not os.path.exists(repo_path):
            print(f"Repository path does not exist: {repo_path}")
            return None

        if fetch_remote:
            # Attempt to fetch from origin, but don't fail the entire process if it doesn't work.
            # This handles cases where the remote might be unreachable (e.g. strict firewall, no remote configured).
            fetch_result = self._execute_git_command(["fetch", "origin"], cwd=repo_path)
            if not fetch_result:
                print(f"Warning: Failed to fetch from origin for {repo_path}. Proceeding with local commit check.")
        
        # Check if the commit exists locally
        commit_exists = self._execute_git_command(["cat-file", "-t", commit_sha], cwd=repo_path)
        if commit_exists != "commit":
            print(f"Commit {commit_sha} not found in local repository {repo_path}.")
            return None

        # Get the diff for the commit
        # git show <commit_sha> --patch
        diff_output = self._execute_git_command(["show", commit_sha, "--patch"], cwd=repo_path)
        if diff_output:
            print(f"Successfully fetched local diff for commit {commit_sha}.")
            return diff_output
        else:
            print(f"Failed to get local diff for commit {commit_sha}.")
            return None

    def cleanup_temp_repos(self):
        """Removes all temporary repositories."""
        if os.path.exists(self.temp_repo_dir):
            print(f"Cleaning up temporary repositories in {self.temp_repo_dir}...")
            shutil.rmtree(self.temp_repo_dir)
            print("Temporary repositories cleaned up.")