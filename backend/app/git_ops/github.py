import re
from dataclasses import dataclass

import httpx

GITHUB_API_URL = "https://api.github.com"

PR_URL_PATTERN = re.compile(r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)")


@dataclass
class PullRequestInfo:
    owner: str
    repo: str
    number: int
    title: str
    base_ref: str
    base_sha: str
    head_ref: str
    head_sha: str
    head_clone_url: str
    html_url: str


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    match = PR_URL_PATTERN.search(url)
    if not match:
        raise ValueError(f"Not a recognizable GitHub pull request URL: {url}")
    return match["owner"], match["repo"], int(match["number"])


def _headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_pull_request(
    owner: str, repo: str, number: int, token: str | None = None
) -> PullRequestInfo:
    """Fetch a pull request's metadata."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{number}"
    response = httpx.get(url, headers=_headers(token), timeout=30)
    response.raise_for_status()
    data = response.json()

    return PullRequestInfo(
        owner=owner,
        repo=repo,
        number=number,
        title=data["title"],
        base_ref=data["base"]["ref"],
        base_sha=data["base"]["sha"],
        head_ref=data["head"]["ref"],
        head_sha=data["head"]["sha"],
        head_clone_url=data["head"]["repo"]["clone_url"],
        html_url=data["html_url"],
    )


def get_pull_request_diff(owner: str, repo: str, number: int, token: str | None = None) -> str:
    """Fetch a pull request's diff as raw unified diff text."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{number}"
    headers = _headers(token)
    headers["Accept"] = "application/vnd.github.v3.diff"
    response = httpx.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text
