import argparse
import sys

from multiplayer.IPClogging.server import server

def main():
    parser = argparse.ArgumentParser(description="Launch a standalone logging server.")
    parser.add_argument(
        "--port", 
        type=int, 
        default=5000, 
        help="Port to listen on (default: 5000)"
    )
    parser.add_argument(
        "--color-mode",
        choices=["level", "origin"],
        default="level",
        help="Coloration mode: 'level' (by criticality) or 'origin' (by message source)"
    )
    
    args = parser.parse_args()
    
    try:
        print(f"Starting standalone logging server on port {args.port}...")
        server(args.port, color_mode=args.color_mode)
    except KeyboardInterrupt:
        print("\nLogging server stopped by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
