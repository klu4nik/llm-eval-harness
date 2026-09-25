"""End-to-end smoke against a real local model. Needs Ollama running and `python -m app.cli index`."""

import pytest

pytestmark = pytest.mark.llm


def test_answerable_question_gets_grounded_answer(real_bot):
    response = real_bot.ask("How can I skip the non-essential actionability checks when clicking?")
    assert not response.refused
    assert "force" in response.answer.lower()
    assert any(c.doc == "actionability" for c in response.contexts)


def test_out_of_scope_question_is_refused(real_bot):
    assert real_bot.ask("How do I configure test retries in Cypress?").refused
