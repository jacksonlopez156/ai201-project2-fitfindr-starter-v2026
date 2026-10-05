"""
Your MCP server. ← UNIT 4, MILESTONE 1

`search_listings` is registered here so any agent speaking MCP can call it.
The other two tools (suggest_outfit, create_fit_card) stay as direct calls
because they call the model and the point of this milestone is to see the seam.

    python mcp_server.py        starts the server (it will just sit there — that's right)
    python mcp_client.py        asks the server what it offers
"""

from mcp.server.fastmcp import FastMCP

from tools import search_listings as _search_listings_impl

# log_level="WARNING" keeps the server from printing an INFO line for every
# request. Without it your terminal fills with "Processing request of type
# CallToolRequest" and the output you actually care about scrolls away.
mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search thrift listings for items matching a description, and optionally a
    size and a price ceiling. Returns a list of matching listing dicts (each
    with id, title, description, category, style_tags, size, condition, price,
    colors, brand, and platform), sorted by keyword overlap score, best match
    first. Returns an empty list when nothing matches — never None.
    max_price is an inclusive ceiling in dollars (float). size is matched
    case-insensitively against whole tokens only, e.g. "M" matches "S/M" but
    not "XL".
    """
    return _search_listings_impl(description, size, max_price)


if __name__ == "__main__":
    mcp.run()
