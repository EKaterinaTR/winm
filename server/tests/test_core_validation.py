"""Tests for core validation (normalize_name)."""
from app.core.validation import normalize_name


def test_normalize_name_strip():
    assert normalize_name("  таверна  ") == "таверна"
    assert normalize_name("\ttavern\t") == "tavern"


def test_normalize_name_lowercase():
    assert normalize_name("Таверна") == "таверна"
    assert normalize_name("TAVERN") == "tavern"


def test_normalize_name_combined():
    assert normalize_name("  Таверна  ") == "таверна"
    assert normalize_name("  ALICE  ") == "alice"


def test_normalize_name_empty_after_trim():
    assert normalize_name("   ") == ""
    assert normalize_name("\t\n") == ""
