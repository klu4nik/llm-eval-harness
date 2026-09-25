"""Tests for the test data itself.

A wrong golden case gives a wrong verdict on every run, so the dataset is
checked before any model is: ids, categories, and that every expected source
exists in the corpus and actually contains the facts the case requires.
"""

import re
from collections import Counter

import pytest

from app.golden import CATEGORIES, load_golden_set

CASES = load_golden_set()


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def test_ids_are_unique(golden_set):
    duplicates = [i for i, n in Counter(c.id for c in golden_set).items() if n > 1]
    assert not duplicates


def test_categories_are_known(golden_set):
    assert {c.category for c in golden_set} <= CATEGORIES


def test_every_category_is_covered(golden_set):
    assert {c.category for c in golden_set} == CATEGORIES


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_refusal_cases_have_no_sources(case):
    if case.should_refuse:
        assert not case.expected_sources and not case.must_mention
    else:
        assert case.expected_sources, "answerable case needs at least one expected source"


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_paraphrase_points_to_existing_case(case, golden_set):
    if case.category == "paraphrase":
        assert case.paraphrase_of in {c.id for c in golden_set}
    else:
        assert case.paraphrase_of is None


@pytest.mark.parametrize("case", [c for c in CASES if not c.should_refuse], ids=lambda c: c.id)
def test_expected_sources_exist_in_corpus(case, corpus_chunks):
    available = {(c.doc, c.section) for c in corpus_chunks}
    missing = [s for s in case.expected_sources if (s.doc, s.section) not in available]
    assert not missing, f"not in corpus: {missing}"


@pytest.mark.parametrize("case", [c for c in CASES if not c.should_refuse], ids=lambda c: c.id)
def test_must_mention_terms_are_grounded_in_sources(case, corpus_chunks):
    """Every required term must appear in the expected sources, otherwise the case asks for facts the bot cannot know."""
    wanted = {(s.doc, s.section) for s in case.expected_sources}
    source_text = _norm(" ".join(c.text for c in corpus_chunks if (c.doc, c.section) in wanted))
    ungrounded = [t for t in case.must_mention if _norm(t) not in source_text]
    assert not ungrounded, f"terms not found in expected sources: {ungrounded}"
