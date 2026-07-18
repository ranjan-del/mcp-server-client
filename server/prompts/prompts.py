"""Prompt templates.

MEMORY.md checklist: MCP Server -> reusable prompt templates.

**Prompts** are the third MCP primitive (alongside tools and resources). They are
parameterised message templates a server offers so that clients/hosts do not each
have to reinvent good wording. A client discovers them, fills in the arguments,
and gets back ready-to-send messages.

We expose two classic ones:

* ``summarize``    -- summarise a blob of text to a target length.
* ``code_review``  -- ask for a focused code review of a snippet.
"""

from __future__ import annotations


def build_summarize_prompt(text: str, style: str = "concise") -> str:
    """Return the user message for a summarisation prompt (pure, testable)."""
    return (
        f"Please provide a {style} summary of the following text. "
        f"Focus on the key points and keep it faithful to the source.\n\n"
        f"---\n{text}\n---"
    )


def build_code_review_prompt(code: str, language: str = "python") -> str:
    """Return the user message for a code-review prompt (pure, testable)."""
    return (
        f"Please review the following {language} code. Comment on correctness, "
        f"readability, edge cases and possible bugs. Be specific and constructive.\n\n"
        f"```{language}\n{code}\n```"
    )


def register(mcp) -> None:
    """Register the reusable prompt templates on the given FastMCP server."""

    @mcp.prompt()
    def summarize(text: str, style: str = "concise") -> str:
        """A prompt that asks the model to summarise the given text.

        Args:
            text: The content to summarise.
            style: Desired style, e.g. "concise", "detailed", "bullet points".
        """
        return build_summarize_prompt(text, style)

    @mcp.prompt()
    def code_review(code: str, language: str = "python") -> str:
        """A prompt that asks the model to review a code snippet.

        Args:
            code: The source code to review.
            language: The programming language of the snippet.
        """
        return build_code_review_prompt(code, language)
