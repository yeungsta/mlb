from pathlib import Path
from smtplib import SMTPRecipientsRefused
from unittest.mock import patch

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


@pytest.fixture
def report_graph(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "src"))
    from models.state import ReportContext, State
    from nodes import report_compiler

    monkeypatch.setattr(report_compiler, "OUTPUT_DIR", tmp_path)
    monkeypatch.setenv("VIN_AI_EMAIL_ENABLED", "1")
    monkeypatch.setenv("VIN_AI_SMTP_SENDER", "sender@example.com")
    monkeypatch.setenv("VIN_AI_SMTP_APP_PASSWORD", "fixture")
    monkeypatch.setenv("VIN_AI_SMTP_RECIPIENT", "default@example.com")

    graph = StateGraph(State, context_schema=ReportContext)
    graph.add_node("report_compiler", report_compiler.report_compiler)
    graph.add_edge(START, "report_compiler")
    graph.add_edge("report_compiler", END)
    return graph.compile(checkpointer=InMemorySaver())


def run_report(graph, context=None):
    return list(graph.stream(
        {"title": "Test report", "summary": "Test summary", "llm_model": "fixture"},
        config={"configurable": {"thread_id": "test-thread"}},
        context=context,
        stream_mode="custom",
    ))


def test_email_choice_is_per_run(report_graph, tmp_path):
    with patch("smtplib.SMTP_SSL") as smtp:
        send = smtp.return_value.__enter__.return_value.send_message

        assert run_report(report_graph, {"report_email": "chosen@example.com"}) == [
            {"type": "report_email", "status": "sent"}
        ]
        assert send.call_args.kwargs["to_addrs"] == ["chosen@example.com"]

        assert run_report(report_graph, {"report_email": None}) == []
        assert send.call_count == 1

        assert run_report(report_graph) == [{"type": "report_email", "status": "sent"}]
        assert send.call_args.kwargs["to_addrs"] == ["default@example.com"]

    assert list(tmp_path.glob("*/*.html"))


@pytest.mark.parametrize("recipient", ["", "first@example.com, second@example.com", "no-domain"])
def test_invalid_recipient_skips_smtp(report_graph, recipient):
    with patch("smtplib.SMTP_SSL") as smtp:
        assert run_report(report_graph, {"report_email": recipient}) == [
            {"type": "report_email", "status": "invalid"}
        ]
        smtp.assert_not_called()


def test_email_disabled_on_server(report_graph, monkeypatch):
    monkeypatch.setenv("VIN_AI_EMAIL_ENABLED", "0")
    with patch("smtplib.SMTP_SSL") as smtp:
        assert run_report(report_graph, {"report_email": "chosen@example.com"}) == [
            {"type": "report_email", "status": "unavailable"}
        ]
        smtp.assert_not_called()


def test_smtp_failure_preserves_report(report_graph, tmp_path):
    with patch("smtplib.SMTP_SSL") as smtp:
        send = smtp.return_value.__enter__.return_value.send_message
        send.side_effect = SMTPRecipientsRefused({})
        assert run_report(report_graph, {"report_email": "chosen@example.com"}) == [
            {"type": "report_email", "status": "failed"}
        ]
    assert list(tmp_path.glob("*/*.html"))
