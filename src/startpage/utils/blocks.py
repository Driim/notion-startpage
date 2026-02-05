"""Notion block construction and manipulation utilities.

This module provides helper functions for creating and appending Notion blocks
to pages, with support for nested block hierarchies.
"""


async def append_block_to_page(notion, page_id: str, block: dict, after: str | None):
    """Recursively append a block with children to a Notion page.

    Separates parent blocks from their children and appends them hierarchically.

    Args:
        notion: Notion AsyncClient instance.
        page_id: Notion page or block ID to append to.
        block: Block dictionary with optional "children" key.
        after: Optional block ID to insert after (for positioning).
    """
    # Separate parent block and children
    parent_block = {k: v for k, v in block.items() if k != "children"}
    children_blocks = block.get("children", [])

    # Append the parent block to the page
    kwargs = {"children": [parent_block]}
    if after is not None:
        kwargs["after"] = after  # type: ignore
    response = await notion.blocks.children.append(page_id, **kwargs)
    parent_id = response["results"][0]["id"]

    # Append the children to the parent block
    if children_blocks:
        # for each child block in children_blocks call append_block_to_page recursively
        # with parent_id
        for child_block in children_blocks:
            await append_block_to_page(notion, parent_id, child_block, after=None)


def create_header_1_block(text: str, children: list) -> dict:
    """Create a toggleable heading_1 block with optional children.

    Args:
        text: Header text content.
        children: List of child block dictionaries.

    Returns:
        Notion heading_1 block dictionary.
    """
    block = {
        "type": "heading_1",
        "heading_1": {
            "is_toggleable": True,
            "rich_text": [{"type": "text", "text": {"content": text}}],
        },
    }

    if children:
        block["children"] = children

    return block


def create_divider_block() -> dict:
    """Create a divider block for visual separation.

    Returns:
        Notion divider block dictionary.
    """
    return {"type": "divider", "divider": {}}
