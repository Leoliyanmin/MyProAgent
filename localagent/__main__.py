
import argparse
from pathlib import Path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Local Agent - AI assistant with file management")
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start in API server mode"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="API server host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port (default: 8000)"
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=None,
        help="Workspace directory (default: current directory)"
    )

    args = parser.parse_args()

    workspace = Path(args.workspace) if args.workspace else Path.cwd()

    if args.api:
        from .api import start_server
        print(f"Starting API server on http://{args.host}:{args.port}")
        print(f"Workspace: {workspace}")
        print(f"Open http://{args.host}:{args.port} in your browser to use the web UI")
        start_server(host=args.host, port=args.port, workspace=workspace)
    else:
        from .cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
