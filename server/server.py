"""MCP server entrypoint (skeleton).

Wires up the tools, resources, and prompt templates described in MEMORY.md and
serves them over the Model Context Protocol.

This is a scaffold only. No feature logic is implemented yet.
"""

# TODO: import the MCP server SDK (see requirements.txt: `mcp`).
# from mcp.server import Server
# from mcp.server.stdio import stdio_server


def build_server():
    """Construct and configure the MCP server instance.

    TODO (MEMORY.md checklist):
      - Register tools: calculator, weather, file_reader, github, database, notes.
      - Expose resources: README, config, files.
      - Register reusable prompt templates.
    """
    # TODO: create the Server object and attach handlers from
    #       server/tools, server/resources, server/prompts.
    raise NotImplementedError("TODO: build MCP server (see MEMORY.md).")


def main() -> None:
    """Run the MCP server over stdio (or another transport)."""
    # TODO: instantiate build_server() and run the stdio transport loop.
    raise NotImplementedError("TODO: run MCP server (see MEMORY.md).")


if __name__ == "__main__":
    main()
