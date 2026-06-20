import sys
import types

from hermes_cli.cli_agent_setup_mixin import CLIAgentSetupMixin


class _FakeConn:
    def execute(self, *_args, **_kwargs):
        pass

    def commit(self):
        pass


class _FakeSessionDB:
    def __init__(self, history):
        self.history = history
        self._conn = _FakeConn()

    def get_session(self, session_id):
        return {"id": session_id, "title": ""}

    def resolve_resume_session_id(self, session_id):
        return session_id

    def get_messages_as_conversation(self, _session_id):
        return list(self.history)


class _CLI(CLIAgentSetupMixin):
    def __init__(self, history):
        self._resumed = True
        self._session_db = _FakeSessionDB(history)
        self.session_id = "session-1"
        self.conversation_history = []
        self.printed = []

    def _console_print(self, message):
        self.printed.append(message)

    def _restore_session_cwd(self, _session_meta):
        pass


def test_cli_preload_resume_preserves_interrupted_tool_tail(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "cli",
        types.SimpleNamespace(_accent_hex=lambda: "cyan"),
    )
    raw_history = [
        {"role": "user", "content": "inspect"},
        {
            "role": "assistant",
            "content": "I will inspect it.",
            "tool_calls": [{"id": "call_1", "function": {"name": "read_file"}}],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "RAW_TOOL_OUTPUT"},
    ]
    cli = _CLI(raw_history)

    assert cli._preload_resumed_session() is True
    assert cli.conversation_history == raw_history


def test_cli_preload_resume_sanitizes_finished_tool_turn(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "cli",
        types.SimpleNamespace(_accent_hex=lambda: "cyan"),
    )
    raw_history = [
        {"role": "user", "content": "inspect"},
        {
            "role": "assistant",
            "content": "I will inspect it.",
            "tool_calls": [{"id": "call_1", "function": {"name": "read_file"}}],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "RAW_TOOL_OUTPUT"},
        {"role": "assistant", "content": "done"},
    ]
    cli = _CLI(raw_history)

    assert cli._preload_resumed_session() is True
    assert cli.conversation_history == [
        {"role": "user", "content": "inspect"},
        {"role": "assistant", "content": "I will inspect it.\n\ndone"},
    ]
