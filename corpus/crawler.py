import json
from typing import Dict

from ApiClient import APIClient


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
        append_object_to_file("./registry_modelcontextprotocol_io/servers.jsonl", info)
