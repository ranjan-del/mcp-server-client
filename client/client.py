"""MCP client (skeleton).

MEMORY.md checklist: connect, list tools, call tools, read resources, streaming.

This is a scaffold only. No feature logic is implemented yet.
"""

# TODO: import the MCP client SDK (see requirements.txt: `mcp`).
# from mcp import ClientSession
# from mcp.client.stdio import stdio_client


async def connect(server_params):
    """Connect to an MCP server and return an initialized session."""
    # TODO: open the transport and initialize a ClientSession.
    raise NotImplementedError("TODO: implement connect (see MEMORY.md).")


async def list_tools(session):
    """List the tools exposed by the connected server."""
    # TODO: call session.list_tools().
    raise NotImplementedError("TODO: implement list_tools (see MEMORY.md).")


async def call_tool(session, name, arguments):
    """Invoke a named tool with the given arguments."""
    # TODO: call session.call_tool(name, arguments).
    raise NotImplementedError("TODO: implement call_tool (see MEMORY.md).")


async def read_resource(session, uri):
    """Read a resource by URI from the connected server."""
    # TODO: call session.read_resource(uri).
    raise NotImplementedError("TODO: implement read_resource (see MEMORY.md).")


async def stream(session, name, arguments):
    """Consume a streaming tool/response from the server."""
    # TODO: iterate streamed chunks from the server.
    raise NotImplementedError("TODO: implement streaming (see MEMORY.md).")


def main() -> None:
    """CLI entrypoint: connect, discover, and demo tool/resource calls."""
    # TODO: parse args, connect, and run a small demo flow.
    raise NotImplementedError("TODO: implement client CLI (see MEMORY.md).")


if __name__ == "__main__":
    main()
