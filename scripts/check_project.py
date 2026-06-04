#!/usr/bin/env python3
"""Project check script for the multiplayer library."""
import os
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(command, cwd=None):
    """Runs a shell command and returns the exit code."""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Check the multiplayer project.")
    parser.add_argument("--fix", action="store_true", help="Automatically fix style errors.")
    parser.add_argument("--force", action="store_true", help="Force check even if only docs changed.")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # In a real scenario, we would check for git changes here.
    # For this task, we assume we always want to run the checks unless specified otherwise.
    
    print("Checking for uv...")
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("uv not found. Please install uv.")
        sys.exit(1)

    print("Installing dependencies...")
    if run_command(["uv", "sync", "--all-extras", "--dev"]) != 0:
        print("Failed to sync dependencies.")
        sys.exit(1)

    print("Running quality checks (Ruff)...")
    ruff_cmd = ["uv", "run", "ruff", "check", "."]
    if args.fix:
        ruff_cmd.append("--fix")
    
    if run_command(ruff_cmd) != 0:
        print("Ruff checks failed.")
        if not args.fix:
            sys.exit(1)

    print("Running type checks (Mypy)...")
    if run_command(["uv", "run", "mypy", "."]) != 0:
        print("Mypy checks failed.")
        sys.exit(1)

    print("Running unit tests (Pytest)...")
    if run_command(["uv", "run", "pytest"]) != 0:
        print("Tests failed.")
        sys.exit(1)

    print("Project check completed successfully.")

if __name__ == "__main__":
    main()
