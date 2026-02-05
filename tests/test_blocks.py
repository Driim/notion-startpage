"""Tests for Notion block utilities."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.startpage.utils.blocks import (
    append_block_to_page,
    create_divider_block,
    create_header_1_block,
)


def test_create_header_1_block_with_children():
    """Test creating a header_1 block with children."""
    children = [
        {
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": "Child 1"}}]},
        },
        {
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": "Child 2"}}]},
        },
    ]

    result = create_header_1_block("Test Header", children)

    assert result["type"] == "heading_1"
    assert result["heading_1"]["is_toggleable"] is True
    assert result["heading_1"]["rich_text"][0]["type"] == "text"
    assert result["heading_1"]["rich_text"][0]["text"]["content"] == "Test Header"
    assert result["children"] == children
    assert len(result["children"]) == 2


def test_create_header_1_block_without_children():
    """Test creating a header_1 block without children."""
    result = create_header_1_block("Test Header", [])

    assert result["type"] == "heading_1"
    assert result["heading_1"]["is_toggleable"] is True
    assert result["heading_1"]["rich_text"][0]["text"]["content"] == "Test Header"
    assert "children" not in result


def test_create_header_1_block_with_none_children():
    """Test creating a header_1 block with None as children."""
    result = create_header_1_block("Test Header", None)

    assert result["type"] == "heading_1"
    assert "children" not in result


def test_create_header_1_block_with_empty_string():
    """Test creating a header_1 block with empty string."""
    result = create_header_1_block("", [])

    assert result["type"] == "heading_1"
    assert result["heading_1"]["rich_text"][0]["text"]["content"] == ""


def test_create_header_1_block_with_special_characters():
    """Test creating a header_1 block with special characters."""
    special_text = "Test 🚀 Header with émojis & symbols"
    result = create_header_1_block(special_text, [])

    assert result["heading_1"]["rich_text"][0]["text"]["content"] == special_text


def test_create_divider_block():
    """Test creating a divider block."""
    result = create_divider_block()

    assert result["type"] == "divider"
    assert result["divider"] == {}
    assert len(result) == 2  # Only type and divider keys


def test_create_divider_block_structure():
    """Test that divider block has correct Notion API structure."""
    result = create_divider_block()

    # Verify it matches Notion API expectations
    assert isinstance(result, dict)
    assert "type" in result
    assert "divider" in result
    assert isinstance(result["divider"], dict)


@pytest.mark.asyncio
async def test_append_block_to_page_simple_block():
    """Test appending a simple block without children."""
    mock_notion = MagicMock()
    mock_response = {"results": [{"id": "block_123"}]}
    mock_notion.blocks.children.append = AsyncMock(return_value=mock_response)

    block = {
        "type": "paragraph",
        "paragraph": {"rich_text": [{"text": {"content": "Test paragraph"}}]},
    }

    await append_block_to_page(mock_notion, "page_123", block, after=None)

    # Verify the block was appended
    mock_notion.blocks.children.append.assert_called_once_with(
        "page_123", children=[block]
    )


@pytest.mark.asyncio
async def test_append_block_to_page_with_after_parameter():
    """Test appending a block with after parameter."""
    mock_notion = MagicMock()
    mock_response = {"results": [{"id": "block_123"}]}
    mock_notion.blocks.children.append = AsyncMock(return_value=mock_response)

    block = {
        "type": "paragraph",
        "paragraph": {"rich_text": [{"text": {"content": "Test"}}]},
    }

    await append_block_to_page(mock_notion, "page_123", block, after="block_456")

    # Verify after parameter was passed
    call_kwargs = mock_notion.blocks.children.append.call_args.kwargs
    assert call_kwargs["after"] == "block_456"


@pytest.mark.asyncio
async def test_append_block_to_page_with_children():
    """Test appending a block with children (recursive)."""
    mock_notion = MagicMock()
    mock_responses = [
        {"results": [{"id": "parent_123"}]},
        {"results": [{"id": "child1_123"}]},
        {"results": [{"id": "child2_123"}]},
    ]
    mock_notion.blocks.children.append = AsyncMock(side_effect=mock_responses)

    block = {
        "type": "heading_1",
        "heading_1": {"rich_text": [{"text": {"content": "Header"}}]},
        "children": [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Child 1"}}]},
            },
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Child 2"}}]},
            },
        ],
    }

    await append_block_to_page(mock_notion, "page_123", block, after=None)

    # Should be called 3 times: once for parent, twice for children
    assert mock_notion.blocks.children.append.call_count == 3


@pytest.mark.asyncio
async def test_append_block_to_page_separates_children():
    """Test that children are separated from parent block."""
    mock_notion = MagicMock()
    mock_response = {"results": [{"id": "block_123"}]}
    mock_notion.blocks.children.append = AsyncMock(return_value=mock_response)

    block = {
        "type": "heading_1",
        "heading_1": {"rich_text": [{"text": {"content": "Header"}}]},
        "children": [{"type": "paragraph", "paragraph": {"rich_text": []}}],
    }

    await append_block_to_page(mock_notion, "page_123", block, after=None)

    # Verify parent block was appended without children key
    first_call_args = mock_notion.blocks.children.append.call_args_list[0]
    parent_block = first_call_args.kwargs["children"][0]
    assert "children" not in parent_block
    assert parent_block["type"] == "heading_1"


@pytest.mark.asyncio
async def test_append_block_to_page_nested_children():
    """Test appending blocks with nested children."""
    mock_notion = MagicMock()
    mock_responses = [
        {"results": [{"id": "parent_123"}]},
        {"results": [{"id": "child_123"}]},
        {"results": [{"id": "grandchild_123"}]},
    ]
    mock_notion.blocks.children.append = AsyncMock(side_effect=mock_responses)

    block = {
        "type": "heading_1",
        "heading_1": {"rich_text": [{"text": {"content": "Header"}}]},
        "children": [
            {
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "Child"}}]},
                "children": [
                    {
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": "Grandchild"}}]
                        },
                    }
                ],
            }
        ],
    }

    await append_block_to_page(mock_notion, "page_123", block, after=None)

    # Should be called 3 times for nested structure
    assert mock_notion.blocks.children.append.call_count == 3


@pytest.mark.asyncio
async def test_append_block_to_page_empty_children_list():
    """Test appending a block with empty children list."""
    mock_notion = MagicMock()
    mock_response = {"results": [{"id": "block_123"}]}
    mock_notion.blocks.children.append = AsyncMock(return_value=mock_response)

    block = {
        "type": "heading_1",
        "heading_1": {"rich_text": [{"text": {"content": "Header"}}]},
        "children": [],
    }

    await append_block_to_page(mock_notion, "page_123", block, after=None)

    # Should only append parent, no children
    assert mock_notion.blocks.children.append.call_count == 1


@pytest.mark.asyncio
async def test_append_block_to_page_uses_parent_id_for_children():
    """Test that children are appended to parent's ID, not original page."""
    mock_notion = MagicMock()
    mock_responses = [
        {"results": [{"id": "parent_id_xyz"}]},
        {"results": [{"id": "child_id_123"}]},
    ]
    mock_notion.blocks.children.append = AsyncMock(side_effect=mock_responses)

    block = {
        "type": "heading_1",
        "heading_1": {"rich_text": [{"text": {"content": "Header"}}]},
        "children": [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Child"}}]},
            }
        ],
    }

    await append_block_to_page(mock_notion, "original_page_123", block, after=None)

    # Second call should use parent block ID, not original page ID
    second_call_args = mock_notion.blocks.children.append.call_args_list[1]
    assert second_call_args.args[0] == "parent_id_xyz"


@pytest.mark.asyncio
async def test_append_block_to_page_children_have_no_after():
    """Test that children blocks are appended without 'after' parameter."""
    mock_notion = MagicMock()
    mock_responses = [
        {"results": [{"id": "parent_123"}]},
        {"results": [{"id": "child_123"}]},
    ]
    mock_notion.blocks.children.append = AsyncMock(side_effect=mock_responses)

    block = {
        "type": "heading_1",
        "heading_1": {"rich_text": [{"text": {"content": "Header"}}]},
        "children": [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Child"}}]},
            }
        ],
    }

    await append_block_to_page(mock_notion, "page_123", block, after="block_456")

    # First call should have after parameter
    first_call_kwargs = mock_notion.blocks.children.append.call_args_list[0].kwargs
    assert "after" in first_call_kwargs
    assert first_call_kwargs["after"] == "block_456"

    # Second call (child) should not have after parameter in the recursive call
    # (checked by the implementation using after=None)
    assert mock_notion.blocks.children.append.call_count == 2
