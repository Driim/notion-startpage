async def append_block_to_page(notion, page_id: str, block: dict, after: str | None):
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
    return {"type": "divider", "divider": {}}
