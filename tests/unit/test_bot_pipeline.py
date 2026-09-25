"""Bot wiring with a fake LLM and a hashing embedder: no model needed."""

from app.bot import SYSTEM_PROMPT, RagBot
from app.config import REFUSAL_TEXT
from tests.conftest import FakeChatModel


def test_ask_returns_answer_contexts_and_latency(offline_retriever, fake_llm):
    response = RagBot(offline_retriever, fake_llm, top_k=3).ask("How do I force a click?")
    assert response.answer == fake_llm.answer
    assert len(response.contexts) == 3
    assert response.model == "fake-llm"
    assert response.latency_ms >= 0
    assert response.refused is False


def test_prompt_contains_numbered_context_and_question(offline_retriever, fake_llm):
    RagBot(offline_retriever, fake_llm, top_k=2).ask("What does force do?")
    system, user = fake_llm.calls[0]
    assert system == SYSTEM_PROMPT
    assert "[1] (" in user and "[2] (" in user
    assert user.rstrip().endswith("Question: What does force do?")


def test_refusal_is_detected(offline_retriever):
    bot = RagBot(offline_retriever, FakeChatModel(REFUSAL_TEXT), top_k=2)
    assert bot.ask("How do I configure Cypress retries?").refused is True


def test_keyword_retrieval_smoke(offline_retriever):
    """Sanity check of the index plumbing, not a quality metric (that needs real embeddings)."""
    hits = offline_retriever.search("abort png jpg images page route", top_k=4)
    assert any(h.doc == "network" and h.section == "Abort requests" for h in hits)
