"""Unit tests for content loader."""

import os
import sys
import tempfile
from unittest import mock
import frontmatter

_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

import content_loader  # noqa: E402  # imported after sys.path adjustment


class TestParseMarkdownPost:
    def test_default_language(self):
        """Test that default language is en-us if omitted."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("---\ntitle: Test\n---\nContent")
            f.flush()
            filepath = f.name

        try:
            # We use a dummy metadata store to avoid writing sidecar metadata
            store = {}
            with mock.patch("content_loader.frontmatter.load") as mock_load:
                post = frontmatter.Post("Content", title="Test")
                mock_load.return_value = post

                # We need to mock calculate_content_hash, which is from helpers
                with mock.patch("content_loader.calculate_content_hash", return_value="hash"):
                    # And mock markdown rendering
                    with mock.patch(
                        "content_loader.render_markdown_with_internal_refs",
                        return_value="<p>Content</p>",
                    ):
                        import pathlib

                        p = pathlib.Path(filepath)
                        result = content_loader.parse_markdown_post(p, _metadata_store=store)

            assert result["lang"] == "en-us"
        finally:
            os.remove(filepath)

    def test_lang_field(self):
        """Test that lang field is correctly extracted."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("---\ntitle: Test\nlang: pt-br\n---\nContent")
            f.flush()
            filepath = f.name

        try:
            store = {}
            with mock.patch("content_loader.frontmatter.load") as mock_load:
                post = frontmatter.Post("Content", title="Test", lang="pt-br")
                mock_load.return_value = post

                with mock.patch("content_loader.calculate_content_hash", return_value="hash"):
                    with mock.patch(
                        "content_loader.render_markdown_with_internal_refs",
                        return_value="<p>Content</p>",
                    ):
                        import pathlib

                        p = pathlib.Path(filepath)
                        result = content_loader.parse_markdown_post(p, _metadata_store=store)

            assert result["lang"] == "pt-br"
        finally:
            os.remove(filepath)

    def test_source_language_field(self):
        """Test that source_language field is correctly extracted if lang is not present."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("---\ntitle: Test\nsource_language: es-es\n---\nContent")
            f.flush()
            filepath = f.name

        try:
            store = {}
            with mock.patch("content_loader.frontmatter.load") as mock_load:
                post = frontmatter.Post("Content", title="Test", source_language="es-es")
                mock_load.return_value = post

                with mock.patch("content_loader.calculate_content_hash", return_value="hash"):
                    with mock.patch(
                        "content_loader.render_markdown_with_internal_refs",
                        return_value="<p>Content</p>",
                    ):
                        import pathlib

                        p = pathlib.Path(filepath)
                        result = content_loader.parse_markdown_post(p, _metadata_store=store)

            assert result["lang"] == "es-es"
        finally:
            os.remove(filepath)
