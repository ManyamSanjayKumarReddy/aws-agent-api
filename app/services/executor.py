# AWS CLI subprocess runner + blocklist
import subprocess
import shlex
import os
import logging

logger = logging.getLogger(__name__)

BLOCKED_PREFIXES = [
    "aws iam delete",
    "aws iam create",
    "aws iam attach",
    "aws iam detach",
    "aws iam put",
    "aws iam update",
    "aws organizations",
    "aws sts assume-role",
]

MAX_OUTPUT_BYTES = 50_000
TIMEOUT_SECONDS = 30


def is_blocked(command: str) -> bool:
    normalized = command.strip().lower()
    return any(normalized.startswith(prefix) for prefix in BLOCKED_PREFIXES)


def run_aws_command(command: str) -> dict:
    command = command.strip()

    if not command.startswith("aws "):
        return {
            "command": command,
            "stdout": "",
            "stderr": "Only AWS CLI commands starting with 'aws' are permitted.",
            "exit_code": 1,
            "blocked": True,
        }

    if is_blocked(command):
        return {
            "command": command,
            "stdout": "",
            "stderr": f"Command blocked by sandbox policy: {command}",
            "exit_code": 1,
            "blocked": True,
        }

    env = os.environ.copy()

    if "--output" not in command:
        command += " --output json"

    logger.info(f"Executing: {command}")

    try:
        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            env=env,
        )

        stdout = result.stdout[:MAX_OUTPUT_BYTES]
        stderr = result.stderr[:MAX_OUTPUT_BYTES]

        if len(result.stdout) > MAX_OUTPUT_BYTES:
            stdout += "\n[Output truncated — exceeded 50KB limit]"

        return {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.returncode,
            "blocked": False,
        }

    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "stdout": "",
            "stderr": f"Command timed out after {TIMEOUT_SECONDS} seconds.",
            "exit_code": 1,
            "blocked": False,
        }
    except FileNotFoundError:
        return {
            "command": command,
            "stdout": "",
            "stderr": "AWS CLI not found. Ensure 'aws' is installed in this environment.",
            "exit_code": 1,
            "blocked": False,
        }
    except Exception as e:
        logger.exception("Unexpected error running command")
        return {
            "command": command,
            "stdout": "",
            "stderr": f"Unexpected error: {str(e)}",
            "exit_code": 1,
            "blocked": False,
        }