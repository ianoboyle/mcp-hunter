import os
import json
from github import Github, Auth, GithubException
from typing import Dict
from ApiClient import APIClient


GITHUB_PAT = os.getenv("GITHUB_PAT")

if not GITHUB_PAT:
    raise Exception("Environment Variable GITHUB_PAT must be present")

GITHUB_AUTH = Auth.Token(GITHUB_PAT)
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
