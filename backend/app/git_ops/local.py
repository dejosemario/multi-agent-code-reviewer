import shutil
from pathlib import Path

from git import GitCommandError, Repo

from app.core.config import get_settings

# The well-known SHA git uses to represent an empty tree — diffing a commit
# against this is how you get the diff for a commit that has no parent.
EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def _workspace_path(workspace_name: str) -> Path:
    settings = get_settings()
    root = Path(settings.workspace_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root / workspace_name


def clone_or_open(repo_url_or_path: str, workspace_name: str) -> Repo:
    """Open a local repo path directly, or clone a remote URL into the workspace dir."""
    local_path = Path(repo_url_or_path)
    if local_path.is_dir() and (local_path / ".git").exists():
        return Repo(local_path)

    dest = _workspace_path(workspace_name)
    if dest.exists():
        shutil.rmtree(dest)
    return Repo.clone_from(repo_url_or_path, dest)


def checkout(repo: Repo, ref: str) -> None:
    """Fetch everything and check out a specific branch, tag, or commit SHA."""
    repo.git.fetch("--all", "--tags")
    repo.git.checkout(ref)


def diff_between_refs(repo: Repo, base_ref: str, head_ref: str) -> str:
    """Unified diff text for what head_ref introduces relative to base_ref."""
    return repo.git.diff(f"{base_ref}...{head_ref}")


def diff_for_commit(repo: Repo, commit_sha: str) -> str:
    """Unified diff text for a single commit against its first parent."""
    commit = repo.commit(commit_sha)
    parent_sha = commit.parents[0].hexsha if commit.parents else EMPTY_TREE_SHA
    return repo.git.diff(parent_sha, commit.hexsha)


def read_file_at_ref(repo: Repo, ref: str, path: str) -> str | None:
    """Read a file's content as of a given ref; None if it doesn't exist there."""
    try:
        return repo.git.show(f"{ref}:{path}")
    except GitCommandError:
        return None


def list_files_at_ref(repo: Repo, ref: str) -> list[str]:
    """List every tracked file path as of a given ref."""
    output = repo.git.ls_tree("-r", "--name-only", ref)
    return output.splitlines() if output else []
