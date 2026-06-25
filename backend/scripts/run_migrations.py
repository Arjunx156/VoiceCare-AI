"""
Migration helper: applies pending Alembic migrations to the production database.
Run with: python scripts/run_migrations.py
"""

import asyncio
import sys
import subprocess
from pathlib import Path

# Resolve backend root
BACKEND_DIR = Path(__file__).resolve().parent.parent
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"


def run_alembic_command(command: list[str]) -> int:
    """Run an Alembic CLI command and return exit code."""
    result = subprocess.run(
        ["alembic", "-c", str(ALEMBIC_INI)] + command,
        cwd=str(BACKEND_DIR),
        capture_output=False,
    )
    return result.returncode


def main():
    import argparse

    parser = argparse.ArgumentParser(description="VoiceCare AI Migration Helper")
    parser.add_argument(
        "command",
        choices=["upgrade", "downgrade", "current", "history", "generate"],
        help="Migration command to run",
    )
    parser.add_argument(
        "--revision",
        default="head",
        help="Target revision (default: head)",
    )
    parser.add_argument(
        "--message",
        default="migration",
        help="Message for auto-generated migrations",
    )

    args = parser.parse_args()

    if args.command == "upgrade":
        print(f"🚀 Upgrading to: {args.revision}")
        code = run_alembic_command(["upgrade", args.revision])

    elif args.command == "downgrade":
        print(f"⏪ Downgrading to: {args.revision}")
        code = run_alembic_command(["downgrade", args.revision])

    elif args.command == "current":
        print("📍 Current revision:")
        code = run_alembic_command(["current"])

    elif args.command == "history":
        print("📋 Migration history:")
        code = run_alembic_command(["history", "--verbose"])

    elif args.command == "generate":
        print(f"✏️  Generating migration: {args.message}")
        code = run_alembic_command(["revision", "--autogenerate", "-m", args.message])

    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        code = 1

    if code != 0:
        print(f"❌ Migration command failed with exit code {code}", file=sys.stderr)
        sys.exit(code)
    else:
        print("✅ Migration command completed successfully.")


if __name__ == "__main__":
    main()
