"""Entry point: `python -m calibre_web_mcp` or `uv run calibre-web-mcp`."""

from .server import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
