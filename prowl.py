import os
import requests
import logging
from github import Github, Auth, GithubException
from typing import Any, Dict, Generator, Optional

from data_adapter import write_registry_item_if_not_exist, write_repository_if_not_exist
from models import RegistryItem

GITHUB_PAT = os.getenv("GITHUB_PAT")

if not GITHUB_PAT:
    raise Exception("Environment Variable GITHUB_PAT must be present")

GITHUB_AUTH = Auth.Token(GITHUB_PAT)


class APIClient:
    def __init__(self, base_url: str, token: Optional[str] = None) -> None:
        self.base_url = base_url
        self.token = token
        self.session = requests.session()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get_items_page(
        self,
        endpoint: Optional[str] = "",
        limit: Optional[int] = 30,
        cursor: Optional[str] = None,
    ) -> Dict:
        params: Dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        url = f"{self.base_url}/{endpoint}" if endpoint else f"{self.base_url}"

        response = self.session.get(url=url, params=params)
        response.raise_for_status()
        return response.json()

    def list(
        self,
        endpoint: Optional[str] = None,
        limit: Optional[int] = 30,
        max_pages: Optional[int] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        current_page = 0
        cursor = None
        while True:
            logging.debug(f"Fetching page {endpoint} page {current_page}")
            if max_pages and current_page >= max_pages:
                break

            page_data = self.get_items_page(endpoint, limit, cursor)
            current_page += 1

            for item in page_data.get("servers", []):
                yield item

            cursor = page_data.get("metadata", {"nextCursor": ""}).get("nextCursor")

            if not cursor:
                break


GithubAPIClient = Github(auth=GITHUB_AUTH)


def _is_open_source(server: Dict) -> bool:
    return server.get("repository", {"source": ""}).get("source") == "github"


def get_model_context_protocol_registry(max_pages: Optional[int] = None) -> None:
    client = APIClient(base_url="https://registry.modelcontextprotocol.io/v0.1/servers")
    for item in client.list(max_pages=max_pages):
        server = item.get("server", {})
        if not _is_open_source(server):
            continue
        write_registry_item_if_not_exist(server)


def _parse_github_url(repo_url: str) -> str:
    return "/".join(repo_url.rstrip("/").split("/")[-2:])


def get_github_repo_data(repo_url: str) -> Dict:
    owner_repo = _parse_github_url(repo_url=repo_url)
    try:
        repo = GithubAPIClient.get_repo(owner_repo)
        logging.debug(f"Fetched github repo {repo_url}")
        return {
            "owner_repo": owner_repo,
            "repo_url": repo_url,
            "stars": repo.stargazers_count,
            "last_pushed": repo.pushed_at.isoformat(),
            "language": repo.language,
            "archived": repo.archived,
            "forks": repo.forks_count,
            "default_branch": repo.default_branch,
        }
    except GithubException as e:
        # 404 = deleted/private since registry scrape
        logging.warning(f"FAILED: Fetched github repo {owner_repo}, status: {e.status}")
        return {"owner_repo": owner_repo, "repo_url": repo_url, "error": e.status}


def fetch_github_repos_for_registry_items():
    registry_items = RegistryItem.select()
    for ri in registry_items:
        logging.debug(f"Fetching github repo for: {ri.name}")
        res = get_github_repo_data(ri.repository)
        write_repository_if_not_exist(
            registry_item=ri,
            data=res,
        )


get_model_context_protocol_registry(max_pages=20)
fetch_github_repos_for_registry_items()
