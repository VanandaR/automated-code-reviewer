import pytest
import os
import sys
import shutil
from unittest.mock import Mock, patch
from main import DiffFetcher
from services.gitlab_service import GitLabService
from services.git_service import GitService
from config import settings

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock settings for testing
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('config.settings.LOCAL_GIT_REPO_PATH', 'test_temp_repos'):
        yield

@pytest.fixture
def gitlab_service_mock():
    """Mock for GitLabService."""
    mock = Mock(spec=GitLabService)
    mock._parse_project_path_from_commit_url.return_value = 'group/subgroup/project'
    mock._parse_commit_sha_from_url.return_value = 'mock_sha123'
    return mock

@pytest.fixture
def git_service_mock():
    """Mock for GitService."""
    mock = Mock(spec=GitService)
    # Ensure cleanup is called
    yield mock
    if os.path.exists(settings.LOCAL_GIT_REPO_PATH):
        shutil.rmtree(settings.LOCAL_GIT_REPO_PATH)

@pytest.fixture
def diff_fetcher(gitlab_service_mock, git_service_mock):
    """Instance of DiffFetcher with mocked services."""
    return DiffFetcher(gitlab_service_mock, git_service_mock)

# --- Test Cases for DiffFetcher ---

def test_fetch_commit_diff_local_success(diff_fetcher, git_service_mock):
    """
    Test that DiffFetcher attempts local git fetching first and succeeds.
    """
    commit_url = "https://gitlab.com/group/subgroup/project/-/commit/mock_sha123"
    expected_diff = "diff --git a/file1.txt b/file1.txt\n--- a/file1.txt\n+++ b/file1.txt\n@@ -1 +1 @@\n-old line\n+new line\n"

    git_service_mock.clone_repository.return_value = "test_temp_repos/project"
    git_service_mock.get_commit_diff.return_value = expected_diff

    diff = diff_fetcher.fetch_commit_diff(commit_url)

    assert diff == expected_diff
    git_service_mock.clone_repository.assert_called_once()
    git_service_mock.get_commit_diff.assert_called_once_with("test_temp_repos/project", "mock_sha123")
    diff_fetcher.gitlab_service.get_commit_diff.assert_not_called()

def test_fetch_commit_diff_fallback_to_gitlab_api_clone_fails(diff_fetcher, git_service_mock):
    """
    Test that DiffFetcher falls back to GitLab API if local cloning fails.
    """
    commit_url = "https://gitlab.com/group/subgroup/project/-/commit/mock_sha123"
    expected_diff_from_gitlab = "gitlab api diff"

    git_service_mock.clone_repository.return_value = None
    diff_fetcher.gitlab_service.get_commit_diff.return_value = expected_diff_from_gitlab

    diff = diff_fetcher.fetch_commit_diff(commit_url)

    assert diff == expected_diff_from_gitlab
    git_service_mock.clone_repository.assert_called_once()
    git_service_mock.get_commit_diff.assert_not_called()
    diff_fetcher.gitlab_service.get_commit_diff.assert_called_once_with(commit_url)

def test_fetch_commit_diff_fallback_to_gitlab_api_get_diff_fails(diff_fetcher, git_service_mock):
    """
    Test that DiffFetcher falls back to GitLab API if local diff fetching fails.
    """
    commit_url = "https://gitlab.com/group/subgroup/project/-/commit/mock_sha123"
    expected_diff_from_gitlab = "gitlab api diff"

    git_service_mock.clone_repository.return_value = "test_temp_repos/project"
    git_service_mock.get_commit_diff.return_value = None # Local diff fetch fails
    diff_fetcher.gitlab_service.get_commit_diff.return_value = expected_diff_from_gitlab

    diff = diff_fetcher.fetch_commit_diff(commit_url)

    assert diff == expected_diff_from_gitlab
    git_service_mock.clone_repository.assert_called_once()
    git_service_mock.get_commit_diff.assert_called_once_with("test_temp_repos/project", "mock_sha123")
    diff_fetcher.gitlab_service.get_commit_diff.assert_called_once_with(commit_url)

def test_fetch_gitlab_mr_diff(diff_fetcher):
    """
    Test that MR diff fetching always uses GitLabService.
    """
    mr_url = "https://gitlab.com/group/subgroup/project/-/merge_requests/123"
    expected_mr_diff = "mr diff from gitlab api"

    diff_fetcher.gitlab_service.get_merge_request_diff.return_value = expected_mr_diff

    diff = diff_fetcher.fetch_gitlab_mr_diff(mr_url)

    assert diff == expected_mr_diff
    diff_fetcher.gitlab_service.get_merge_request_diff.assert_called_once_with(mr_url)
    diff_fetcher.git_service.clone_repository.assert_not_called() # Ensure local git is not used for MRs
    diff_fetcher.git_service.get_commit_diff.assert_not_called()

# --- Test Cases for GitService (Integrity tests for parsing/cloning logic) ---

@pytest.fixture
def real_git_service():
    """Fixture for real GitService, ensuring cleanup."""
    service = GitService()
    yield service
    service.cleanup_temp_repos()

def test_get_repo_name_from_url_mr_url(real_git_service):
    mr_url = "https://gitlab.customs.go.id/rest-api/smart-pcc-perencanaan/-/merge_requests/123"
    repo_name = real_git_service._get_repo_name_from_url(mr_url)
    assert repo_name == "smart-pcc-perencanaan"

def test_get_repo_name_from_url_commit_url(real_git_service):
    commit_url = "https://gitlab.customs.go.id/rest-api/smart-pcc-perencanaan/commit/c7ffb5ffa55bb5d437b67780d1138033f01e7a20"
    repo_name = real_git_service._get_repo_name_from_url(commit_url)
    assert repo_name == "smart-pcc-perencanaan"

def test_get_repo_name_from_url_direct_repo_url(real_git_service):
    repo_url = "https://gitlab.com/some_group/another_project.git"
    repo_name = real_git_service._get_repo_name_from_url(repo_url)
    assert repo_name == "another_project"

def test_get_repo_name_from_url_direct_repo_url_no_git(real_git_service):
    repo_url = "https://gitlab.com/some_group/another_project"
    repo_name = real_git_service._get_repo_name_from_url(repo_url)
    assert repo_name == "another_project"

@patch('subprocess.run')
def test_clone_repository_new_clone(mock_subprocess_run, real_git_service):
    mock_subprocess_run.return_value = Mock(stdout="Cloned successfully", stderr="", returncode=0)
    repo_url = "https://gitlab.com/test_group/test_project.git"
    
    with patch('os.path.exists', return_value=False): # Simulate repo not existing
        repo_path = real_git_service.clone_repository(repo_url)
        assert repo_path == os.path.join(settings.LOCAL_GIT_REPO_PATH, "test_project")
        mock_subprocess_run.assert_called_with(
            ['git', 'clone', repo_url, repo_path],
            cwd=settings.LOCAL_GIT_REPO_PATH,
            capture_output=True, text=True, check=True
        )

@patch('subprocess.run')
def test_clone_repository_existing_pull(mock_subprocess_run, real_git_service):
    mock_subprocess_run.return_value = Mock(stdout="Already up to date", stderr="", returncode=0)
    repo_url = "https://gitlab.com/test_group/test_project.git"
    repo_name = real_git_service._get_repo_name_from_url(repo_url)
    repo_path = os.path.join(settings.LOCAL_GIT_REPO_PATH, repo_name)
    
    with patch('os.path.exists', return_value=True): # Simulate repo existing
        with patch('shutil.rmtree') as mock_rmtree:
            repo_path_result = real_git_service.clone_repository(repo_url)
            assert repo_path_result == repo_path
            mock_subprocess_run.assert_called_with(
                ['git', 'pull'],
                cwd=repo_path,
                capture_output=True, text=True, check=True
            )
            mock_rmtree.assert_not_called() # Should not remove for pull

@patch('subprocess.run')
def test_get_commit_diff_success(mock_subprocess_run, real_git_service):
    expected_diff = "some diff content"
    # The sequence of git commands: fetch, cat-file -t, show
    mock_subprocess_run.side_effect = [
        Mock(stdout="Fetched origin", stderr="", returncode=0), # For git fetch origin
        Mock(stdout="commit", stderr="", returncode=0), # For git cat-file -t <commit_sha>
        Mock(stdout=expected_diff, stderr="", returncode=0) # For git show <commit_sha> --patch
    ]
    repo_path = os.path.join(settings.LOCAL_GIT_REPO_PATH, "project") # Use os.path.join for consistency
    commit_sha = "abcdef12345"

    with patch('os.path.exists', return_value=True): # Simulate repo path existing
        diff = real_git_service.get_commit_diff(repo_path, commit_sha)
        assert diff == expected_diff
        # Assert calls in sequence
        calls = mock_subprocess_run.call_args_list
        assert len(calls) == 3
        calls[0].assert_called_with(['git', 'fetch', 'origin'], cwd=repo_path, capture_output=True, text=True, check=True)
        calls[1].assert_called_with(['git', 'cat-file', '-t', commit_sha], cwd=repo_path, capture_output=True, text=True, check=True)
        calls[2].assert_called_with(['git', 'show', commit_sha, '--patch'], cwd=repo_path, capture_output=True, text=True, check=True)