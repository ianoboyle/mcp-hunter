import os
import json
import requests
from github import Github, Auth, GithubException
from typing import Any, Dict, Generator, Optional

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


def append_object_to_file(path: str, obj: Dict) -> None:
    with open(path, "a") as f:
        f.write(json.dumps(obj) + "\n")


def is_open_source(server: Dict) -> bool:
    return server.get("repository", {"source": ""}).get("source") == "github"


def get_model_context_protocol_registry() -> None:
    client = APIClient(base_url="https://registry.modelcontextprotocol.io/v0.1/servers")

    for item in client.list(max_pages=100):
        server = item.get("server", {})
        if not is_open_source(server):
            continue

        info = {
            "schema": server.get("$schema"),
            "name": server.get("name"),
            "remotes": server.get("remotes"),
            "repository": server.get("repository"),
        }
        append_object_to_file("./data/servers/servers.jsonl", info)


def dedupe_repos() -> None:
    big_set = set()
    with open("./data/servers/servers.jsonl") as f:
        for line in f.readlines():
            obj = json.loads(line)
            url = obj.get("repository", {"url": ""}).get("url")
            if url in big_set:
                continue
            big_set.add(url)
            append_object_to_file("./data/repos/repos.jsonl", obj)


def _parse_github_url(repo_url: str) -> str:
    return "/".join(repo_url.rstrip("/").split("/")[-2:])


def get_github_repo_data(repo_url: str) -> Dict:
    owner_repo = _parse_github_url(repo_url=repo_url)
    try:
        repo = GithubAPIClient.get_repo(owner_repo)
        return {
            "repo": owner_repo,
            "repo_url": repo_url,
            "stars": repo.stargazers_count,
            "last_push": repo.pushed_at.isoformat(),
            "language": repo.language,
            "archived": repo.archived,
            "forks": repo.forks_count,
            "default_branch": repo.default_branch,
        }
    except GithubException as e:
        # 404 = deleted/private since registry scrape
        return {"repo": owner_repo, "error": e.status}


def enrich_repos() -> None:
    with open("./data/repos/repos.jsonl") as f:
        for line in f.readlines():
            obj = json.loads(line)
            url = obj.get("repository", {"url": ""}).get("url")
            enriched_data = get_github_repo_data(repo_url=url)
            append_object_to_file("./data/repos/enriched_repos.jsonl", enriched_data)


enrich_repos()
