import logging
import subprocess
from pathlib import Path
from models import Repository
from config import FETCHED_REPOSITORY_DATA_DIR


def clone_repo(repo_url: str, dest_dir: str, commit_sha: str | None = None) -> Path:
    dest = Path(dest_dir)
    if dest.exists():
        return dest  # already cloned, skip

    cmd = ["git", "clone", "--depth", "1"]
    if commit_sha:
        cmd = [
            "git",
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            repo_url,
            str(dest),
        ]
        subprocess.run(cmd, check=True, timeout=120)
        subprocess.run(["git", "-C", str(dest), "checkout", commit_sha], check=True)
        return dest

    cmd += [repo_url, str(dest)]
    logging.debug(f"fetcher running {cmd}")
    subprocess.run(cmd, check=True, timeout=120)
    return dest


def clone_repositories(ecosystem: str) -> None:
    for repo in Repository.select().filter(ecosystem=ecosystem, active=True):
        clone_repo(
            repo_url=repo.repo_url,
            dest_dir=f"{FETCHED_REPOSITORY_DATA_DIR}/{repo.owner_repo}",
        )


clone_repositories("Python")
