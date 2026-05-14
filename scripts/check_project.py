import subprocess
import sys
import os
import shutil
import argparse
from pathlib import Path

def run_command(command, shell=True, check=True):
    """Executes a shell command and returns the result."""
    try:
        result = subprocess.run(command, shell=shell, check=check, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error while executing command: {' '.join(command) if isinstance(command, list) else command}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        if check:
            sys.exit(e.returncode)
        return None

def check_uv():
    """Checks if 'uv' is installed, and installs it if not."""
    print("Checking 'uv' installation...")
    if shutil.which("uv"):
        print("'uv' is already installed.")
        return True
    
    print("'uv' not found. Attempting to install 'uv'...")
    try:
        # Installation via pip
        subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
        print("'uv' was successfully installed via pip.")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install 'uv' via pip.")
        # Alternative method via PowerShell for Windows
        print("Attempting alternative installation (PowerShell script)...")
        ps_cmd = "powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\""
        try:
            subprocess.run(ps_cmd, shell=True, check=True)
            print("'uv' was installed via the PowerShell script.")
            return True
        except subprocess.CalledProcessError:
            print("Fatal error: Could not install 'uv'. Please install it manually: https://astral.sh/uv")
            sys.exit(1)

def get_changed_files(target_file=None):
    """Returns a list of changed files compared to origin/main or the parent commit."""
    if target_file:
        return [str(target_file)]
    
    try:
        # We try to get the diff against origin/main, if it fails we take the current changes
        # vs the last commit.
        base = "origin/main"
        # Check if origin/main exists
        subprocess.run(["git", "rev-parse", "--verify", base], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        base = "HEAD"

    try:
        output = subprocess.check_output(["git", "diff", "--name-only", base], text=True)
        files = output.splitlines()
        
        # We also add unstaged changes (new files not yet in git)
        output_unstaged = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], text=True)
        files.extend(output_unstaged.splitlines())
        
        return list(set(files))
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git not available or not a git repo
        return None

def main():
    parser = argparse.ArgumentParser(description="Verify syntax and run project unit tests in an isolated environment.")
    parser.add_argument("--fix", action="store_true", help="Ask Ruff to fix detectable errors.")
    parser.add_argument("--force", action="store_true", help="Force execution even if only documentation has changed.")
    parser.add_argument("--only", type=str, help="Only check the specified file.")
    args = parser.parse_args()

    # Ensure we are at the project root
    project_root = Path(__file__).parent.parent.resolve()
    os.chdir(project_root)

    # Detect changes to avoid useless runs
    if not args.force:
        changed_files = get_changed_files(args.only)
        if changed_files is not None:
            # We filter for relevant files: .py files or files in src/ or tests/
            # and we exclude documentation files.
            important_extensions = {".py", ".toml", ".lock"}
            important_dirs = {"src", "tests", "scripts"}
            
            needs_check = False
            for f in changed_files:
                path = Path(f)
                if path.suffix in important_extensions:
                    needs_check = True
                    break
                # Check if file is in an important directory
                if any(part in important_dirs for part in path.parts):
                    needs_check = True
                    break
            
            if not needs_check and changed_files:
                print("\n--- Skip Check ---")
                print("Only documentation or non-code files have changed.")
                print("Use --force to run checks anyway.")
                return

    # 1. Check/Install uv
    check_uv()
    
    # 2. Run Ruff (syntax/linting) for multiple Python versions
    print("\n--- Syntax check with Ruff ---")
    python_versions = ["3.12", "3.13", "3.14"]
    for py_ver in python_versions:
        print(f"\nChecking syntax for Python {py_ver}...")
        try:
            # We use --no-project to ensure total isolation from the project's venv
            # We specify the python version to ensure consistency
            cmd_ruff = ["uv", "run", "--no-project", "--python", py_ver, "--with", "ruff", "ruff", "check", "."]
            if args.fix:
                cmd_ruff.append("--fix")
                print("Auto-fix mode enabled (--fix)")
                
            subprocess.run(cmd_ruff, check=True)
            print(f"Ruff check successful for Python {py_ver}!")
        except subprocess.CalledProcessError as e:
            print(f"Ruff found syntax or style issues for Python {py_ver}.")
            sys.exit(e.returncode)
    
    # 3. Run unit tests in an isolated environment
    print("\n--- Running unit tests in an isolated environment ---")
    try:
        # Configure PYTHONPATH to include project sources
        env = os.environ.copy()
        abs_src = str(project_root / "src")
        # Ensure project folders are in the PYTHONPATH
        # In CI, PYTHONPATH is often set to 'src'
        env["PYTHONPATH"] = f"{abs_src}{os.pathsep}{env.get('PYTHONPATH', '')}"
        
        # We use 'uv run' with --no-project to force an environment separate from the project's
        # We install the project with its dev dependencies in editable mode
        # We ALSO run a check for the data files to ensure they are discoverable
        check_data_cmd = [
            "uv", "run",
            "--no-project",
            "--python", "3.12",
            "--with-editable", ".[dev]",
            "python", "-c", 
            "from multiplayer.utils import _get_names_from_source; " 
            "import sys; "
            "sources = ['data/cities.csv', 'data/roman_gods.csv']; "
            "results = [(s, _get_names_from_source(s)) for s in sources]; "
            "[print(f'Checking {s}... Found: {len(r) if r else \"None\"}') for s, r in results]; "
            "sys.exit(0 if all(r and len(r) > 0 for s, r in results) else 1)"
        ]
        
        print("Verifying data file access in isolated environment...")
        subprocess.run(check_data_cmd, env=env, check=True)
        print("Data file access verified!")

        cmd = [
            "uv", "run", 
            "--no-project", 
            "--python", "3.12",
            "--with-editable", ".[dev]", 
            "pytest"
        ]
        
        subprocess.run(cmd, env=env, check=True)
        print("\nAll tests passed successfully!")
    except subprocess.CalledProcessError:
        print("\nVerification or tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
