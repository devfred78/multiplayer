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

def main():
    parser = argparse.ArgumentParser(description="Verify syntax and run project unit tests in an isolated environment.")
    parser.add_argument("--fix", action="store_true", help="Ask Ruff to fix detectable errors.")
    args = parser.parse_args()

    # Ensure we are at the project root
    project_root = Path(__file__).parent.parent.resolve()
    os.chdir(project_root)
    
    # 1. Check/Install uv
    check_uv()
    
    # 2. Run Ruff (syntax/linting)
    print("\n--- Syntax check with Ruff ---")
    try:
        # We use --no-project to ensure total isolation from the project's venv
        # We specify the python version to ensure consistency
        cmd_ruff = ["uv", "run", "--no-project", "--python", "3.14", "--with", "ruff", "ruff", "check", "."]
        if args.fix:
            cmd_ruff.append("--fix")
            print("Auto-fix mode enabled (--fix)")
            
        subprocess.run(cmd_ruff, check=True)
        print("Ruff check successful!")
    except subprocess.CalledProcessError as e:
        print("Ruff found syntax or style issues.")
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
            "--python", "3.14",
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
            "--python", "3.14", 
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
