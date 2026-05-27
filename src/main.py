"""SEO Tool - Main entry point.

Usage:
    python -m src.main serve          # Start web server
    python -m src.main init-db        # Initialize database
    python -m src.main --help         # Show help

Or use the CLI:
    seo analyze https://example.com
    seo crawl https://example.com
    seo --help
"""

import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def main():
    """Main entry point - delegates to CLI."""
    from src.cli.commands import cli
    cli()


def serve():
    """Start the FastAPI web server."""
    import uvicorn
    from src.api import create_app
    from src.utils.config import settings

    app = create_app()
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )


def init_db():
    """Initialize the database and data directories."""
    from src.utils.config import settings

    # Create required directories
    dirs = [
        settings.data_dir,
        settings.reports_dir,
        project_root / "logs",
        project_root / "static",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {d}")

    print("\nDatabase and directories initialized successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "serve":
            serve()
        elif command == "init-db":
            init_db()
        else:
            main()
    else:
        main()
