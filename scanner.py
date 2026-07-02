import subprocess
import logging
import json
from config import SEMGREP_RULES_DIR


def run_semgrep(target_dir: str, rules_dir: str = SEMGREP_RULES_DIR) -> list[dict]:
    result = subprocess.run(
        [
            "semgrep",
            "--config",
            rules_dir,
            "--json",
            "--quiet",
            target_dir,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode not in (0, 1):  # 1 = findings present, still success
        logging.debug(result)
        raise RuntimeError(f"Semgrep failed: {result.stderr}")

    import pdb

    pdb.set_trace()
    output = json.loads(result.stdout)
    return output["results"]


res = run_semgrep("repos/anomalyarmor/agents")
print(res)
