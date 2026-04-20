import argparse
import sys
from pathlib import Path

# Add src to sys.path to allow imports from multiplayer
project_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(project_root / "src"))

try:
    from multiplayer.IPClogging.server import server
except ImportError:
    print("Error: Could not import multiplayer.IPClogging.server.")
    print("Make sure you are running this script from the project root or 'src' is in your PYTHONPATH.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Launch a standalone logging server.")
    parser.add_argument(
        "--port", 
        type=int, 
        default=5000, 
        help="Port to listen on (default: 5000)"
    )
    
    args = parser.parse_args()
    
    try:
        print(f"Starting standalone logging server on port {args.port}...")
        server(args.port)
    except KeyboardInterrupt:
        print("\nLogging server stopped by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
