"""
test_beta.py — Unit tests for Engine Beta (Semantic RAG Engine).

Uses the `rag_engine` session fixture from conftest.py.
Run with: pytest tests/test_beta.py -v

NOTE: The first run initializes dummy data in LanceDB and downloads embeddings.
      Subsequent runs are significantly faster.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")


def test_general_search_returns_blight_guide(rag_engine):
    """
    A general blight query without filters must retrieve the tomato blight guideline.
    Verifies that the source citation is present in the output.
    """
    result = rag_engine.search(query="How do I manage early blight?")
    assert "guide_tomato_blight_ne_01" in result, (
        f"Expected tomato blight guide in unfiltered results, got:\n{result}"
    )


def test_filtered_search_returns_correct_crop_guide(rag_engine):
    """
    A search filtered by crop='corn' and zone='5a' must return the corn soil guide,
    confirming metadata pre-filtering is working correctly.
    """
    result = rag_engine.search(
        query="soil requirements and pH levels",
        metadata_filters={"crop_tags": ["corn"], "hardiness_zones": "5a"}
    )
    assert "guide_corn_soil_ph" in result, (
        f"Expected corn soil guide with crop+zone filters, got:\n{result}"
    )


def test_filter_prevents_cross_crop_contamination(rag_engine):
    """
    A search filtered to 'apples' must NOT return tomato guidelines,
    verifying that metadata pre-filtering prevents cross-crop contamination (FR-3).
    """
    result = rag_engine.search(
        query="tomatoes",
        metadata_filters={"crop_tags": ["apples"]}
    )
    assert "guide_tomato_blight_ne_01" not in result, (
        f"Tomato guide should NOT appear when filtering for apples:\n{result}"
    )


def test_empty_query_returns_structured_response(rag_engine):
    """
    Even with an unusual query, the engine must return a structured markdown
    response starting with the expected section header (NFR-5 graceful failure).
    """
    result = rag_engine.search(query="xyzzy nonexistent topic 12345")
    assert "AGRICORE MCP: COMMUNITY GUIDELINES" in result, (
        f"Expected structured markdown header in all responses, got:\n{result}"
    )
