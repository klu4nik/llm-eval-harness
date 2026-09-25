"""End-to-end smoke against a real local model. Needs Ollama running and `python -m app.cli index`."""

import pytest

pytestmark = pytest.mark.llm


@pytest.fixture(scope="module")
def bot():
    ollama = pytest.importorskip("ollama")
    from app.config import Settings

    try:
        ollama.Client(host=Settings().ollama_host).list()
    except Exception:
        pytest.skip("Ollama is not reachable")
    from app.factory import build_bot

    return build_bot()


def test_answerable_question_gets_grounded_answer(bot):
    response = bot.ask("How can I skip the non-essential actionability checks when clicking?")
    assert not response.refused
    assert "force" in response.answer.lower()
    assert any(c.doc == "actionability" for c in response.contexts)


def test_out_of_scope_question_is_refused(bot):
    assert bot.ask("How do I configure test retries in Cypress?").refused
