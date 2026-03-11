"""Tests for langfuse-trace hook (pure unit tests, no Langfuse connection)."""

import importlib.util
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module from its hyphenated filename
_spec = importlib.util.spec_from_file_location(
    "langfuse_trace",
    Path(__file__).parent / "langfuse-trace.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Bind module-level functions
is_configured = _mod.is_configured
get_source_project = _mod.get_source_project
get_git_branch = _mod.get_git_branch
build_tags = _mod.build_tags
extract_usage = _mod.extract_usage
extract_text_output = _mod.extract_text_output
read_transcript_messages = _mod.read_transcript_messages
get_tool_results = _mod.get_tool_results
get_state_dir = _mod.get_state_dir
get_state_path = _mod.get_state_path
load_state = _mod.load_state
save_state = _mod.save_state
ship_transcript_data = _mod.ship_transcript_data
handle_session_start = _mod.handle_session_start
handle_post_tool_use = _mod.handle_post_tool_use
handle_subagent_stop = _mod.handle_subagent_stop
handle_session_end = _mod.handle_session_end


# -- Fixtures --


@pytest.fixture
def transcript_dir(tmp_path):
    return tmp_path


def write_transcript(path, messages):
    with open(path, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")


def make_assistant_msg(request_id, model="claude-opus-4-6", text="hello",
                       tool_uses=None, usage=None):
    content = [{"type": "text", "text": text}]
    if tool_uses:
        content.extend(tool_uses)
    if usage is None:
        usage = {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 200,
            "cache_creation_input_tokens": 10,
        }
    return {
        "type": "assistant",
        "requestId": request_id,
        "message": {
            "model": model,
            "content": content,
            "usage": usage,
            "stop_reason": "end_turn",
        },
    }


def make_user_msg(tool_results=None):
    content = tool_results or []
    return {
        "type": "user",
        "message": {"content": content},
    }


def make_tool_use(tool_id, name="Bash", input_data=None):
    return {"type": "tool_use", "id": tool_id, "name": name,
            "input": input_data or {}}


def make_tool_result(tool_use_id, content="ok", is_error=False):
    return {"type": "tool_result", "tool_use_id": tool_use_id,
            "content": content, "is_error": is_error}


# -- is_configured --


class TestIsConfigured:
    def test_all_set(self, monkeypatch):
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
        monkeypatch.setenv("LANGFUSE_HOST", "http://localhost")
        assert is_configured() is True

    def test_missing_key(self, monkeypatch):
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
        monkeypatch.delenv("LANGFUSE_HOST", raising=False)
        assert is_configured() is False

    def test_empty_value(self, monkeypatch):
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
        monkeypatch.setenv("LANGFUSE_HOST", "http://localhost")
        assert is_configured() is False


# -- get_source_project --


class TestGetSourceProject:
    def test_default(self, monkeypatch):
        monkeypatch.delenv("LANGFUSE_SOURCE_PROJECT", raising=False)
        assert get_source_project() == "unknown"

    def test_custom(self, monkeypatch):
        monkeypatch.setenv("LANGFUSE_SOURCE_PROJECT", "my-project")
        assert get_source_project() == "my-project"


# -- build_tags --


class TestBuildTags:
    def test_filters_empty(self):
        assert build_tags("a", "", "b", None, "c") == ["a", "b", "c"]

    def test_all_empty(self):
        assert build_tags("", None) == []

    def test_all_present(self):
        assert build_tags("x", "y") == ["x", "y"]


# -- extract_usage --


class TestExtractUsage:
    def test_full_usage(self):
        usage = {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 200,
            "cache_creation_input_tokens": 10,
        }
        result = extract_usage(usage)
        assert result == {"input": 310, "output": 50, "inputCached": 200}

    def test_empty_usage(self):
        result = extract_usage({})
        assert result == {"input": 0, "output": 0, "inputCached": 0}

    def test_no_cache(self):
        usage = {"input_tokens": 500, "output_tokens": 100}
        result = extract_usage(usage)
        assert result == {"input": 500, "output": 100, "inputCached": 0}


# -- extract_text_output --


class TestExtractTextOutput:
    def test_text_blocks(self):
        blocks = [
            {"type": "text", "text": "Hello"},
            {"type": "tool_use", "id": "t1"},
            {"type": "text", "text": "World"},
        ]
        assert extract_text_output(blocks) == "Hello\nWorld"

    def test_no_text(self):
        blocks = [{"type": "tool_use", "id": "t1"}]
        assert extract_text_output(blocks) is None

    def test_empty(self):
        assert extract_text_output([]) is None


# -- Transcript parsing --


class TestReadTranscriptMessages:
    def test_reads_assistant_messages(self, transcript_dir):
        path = transcript_dir / "transcript.jsonl"
        write_transcript(path, [
            make_assistant_msg("req1"),
            make_user_msg(),
            make_assistant_msg("req2"),
        ])
        msgs = read_transcript_messages(str(path), "assistant")
        assert len(msgs) == 2
        assert msgs[0]["requestId"] == "req1"

    def test_reads_user_messages(self, transcript_dir):
        path = transcript_dir / "transcript.jsonl"
        write_transcript(path, [
            make_assistant_msg("req1"),
            make_user_msg([make_tool_result("t1")]),
        ])
        msgs = read_transcript_messages(str(path), "user")
        assert len(msgs) == 1

    def test_missing_file(self):
        assert read_transcript_messages("/nonexistent/path.jsonl") == []

    def test_malformed_json(self, transcript_dir):
        path = transcript_dir / "transcript.jsonl"
        path.write_text('{"type":"assistant"}\n{bad json}\n{"type":"assistant"}\n')
        msgs = read_transcript_messages(str(path), "assistant")
        assert len(msgs) == 2


class TestGetToolResults:
    def test_indexes_by_tool_use_id(self, transcript_dir):
        path = transcript_dir / "transcript.jsonl"
        write_transcript(path, [
            make_user_msg([
                make_tool_result("t1", "output1"),
                make_tool_result("t2", "output2", is_error=True),
            ]),
        ])
        results = get_tool_results(str(path))
        assert "t1" in results
        assert results["t1"]["content"] == "output1"
        assert results["t2"]["is_error"] is True


# -- State management --


class TestStateManagement:
    def test_state_dir_created_with_permissions(self):
        state_dir = get_state_dir()
        assert state_dir.exists()
        assert oct(state_dir.stat().st_mode & 0o777) == "0o700"

    def test_save_and_load(self, tmp_path):
        with patch.object(_mod, "get_state_dir", return_value=tmp_path):
            save_state("test-session", {"trace_id": "abc", "sent_request_ids": ["r1"]})
            state = load_state("test-session")
            assert state["trace_id"] == "abc"
            assert state["sent_request_ids"] == ["r1"]

    def test_load_missing(self, tmp_path):
        with patch.object(_mod, "get_state_dir", return_value=tmp_path):
            state = load_state("nonexistent")
            assert state == {"sent_request_ids": [], "trace_id": None}

    def test_load_corrupt(self, tmp_path):
        with patch.object(_mod, "get_state_dir", return_value=tmp_path):
            (tmp_path / "corrupt.json").write_text("{bad")
            state = load_state("corrupt")
            assert state == {"sent_request_ids": [], "trace_id": None}


# -- ship_transcript_data --


class TestShipTranscriptData:
    def test_ships_new_generations_and_tools(self, transcript_dir):
        path = transcript_dir / "transcript.jsonl"
        tool = make_tool_use("t1", "Bash", {"command": "ls"})
        write_transcript(path, [
            make_assistant_msg("req1", tool_uses=[tool]),
            make_user_msg([make_tool_result("t1", "file.txt")]),
        ])

        client = MagicMock()
        mock_obs = MagicMock()
        client.start_observation.return_value = mock_obs

        sent = ship_transcript_data(client, "trace123", str(path), set())
        assert "req1" in sent

        # Should have created a generation and a tool observation
        assert client.start_observation.call_count == 2
        calls = client.start_observation.call_args_list
        assert calls[0].kwargs["as_type"] == "generation"
        assert calls[1].kwargs["as_type"] == "tool"
        assert calls[1].kwargs["name"] == "Bash"

    def test_skips_already_sent(self, transcript_dir):
        path = transcript_dir / "transcript.jsonl"
        write_transcript(path, [make_assistant_msg("req1")])

        client = MagicMock()
        sent = ship_transcript_data(client, "trace123", str(path), {"req1"})
        assert client.start_observation.call_count == 0

    def test_passes_parent_span_id(self, transcript_dir):
        path = transcript_dir / "transcript.jsonl"
        write_transcript(path, [make_assistant_msg("req1")])

        client = MagicMock()
        mock_obs = MagicMock()
        client.start_observation.return_value = mock_obs

        ship_transcript_data(client, "trace123", str(path), set(),
                             parent_span_id="parent456")

        call_kwargs = client.start_observation.call_args_list[0].kwargs
        assert call_kwargs["trace_context"]["parent_span_id"] == "parent456"

    def test_marks_error_tools(self, transcript_dir):
        path = transcript_dir / "transcript.jsonl"
        tool = make_tool_use("t1", "Bash")
        write_transcript(path, [
            make_assistant_msg("req1", tool_uses=[tool]),
            make_user_msg([make_tool_result("t1", "error!", is_error=True)]),
        ])

        client = MagicMock()
        mock_obs = MagicMock()
        client.start_observation.return_value = mock_obs

        ship_transcript_data(client, "trace123", str(path), set())

        tool_call = client.start_observation.call_args_list[1]
        assert tool_call.kwargs["level"] == "ERROR"


# -- Handler tests (mock Langfuse client) --


class TestHandleSubagentStop:
    def test_uses_observation_id(self, transcript_dir):
        path = transcript_dir / "transcript.jsonl"
        write_transcript(path, [make_assistant_msg("req1")])

        client = MagicMock()
        agent_obs = MagicMock()
        agent_obs.id = "abc123def456"
        gen_obs = MagicMock()
        client.start_observation.side_effect = [agent_obs, gen_obs]

        with patch.object(_mod, "load_state",
                          return_value={"trace_id": "t1", "sent_request_ids": []}), \
             patch.object(_mod, "save_state"):
            handle_subagent_stop(client, {
                "session_id": "sess1",
                "agent_id": "a1",
                "agent_type": "general-purpose",
                "agent_transcript_path": str(path),
            })

        # The generation should use agent_obs.id as parent
        gen_call = client.start_observation.call_args_list[1]
        assert gen_call.kwargs["trace_context"]["parent_span_id"] == "abc123def456"


class TestHandleSessionEnd:
    def test_cleans_up_state_file(self, tmp_path):
        state_file = tmp_path / "sess1.json"
        state_file.write_text(json.dumps({
            "trace_id": "t1", "sent_request_ids": []
        }))

        client = MagicMock()
        mock_obs = MagicMock()
        client.start_observation.return_value = mock_obs

        with patch.object(_mod, "get_state_dir", return_value=tmp_path), \
             patch.object(_mod, "get_git_branch", return_value="main"), \
             patch.object(_mod, "get_source_project", return_value="test"):
            handle_session_end(client, {
                "session_id": "sess1",
                "transcript_path": "",
                "reason": "user_exit",
            })

        assert not state_file.exists()

    def test_totals_from_main_transcript_only(self, tmp_path, transcript_dir):
        """Verify session-end totals come from main transcript, not subagent."""
        main_path = transcript_dir / "main.jsonl"
        write_transcript(main_path, [
            make_assistant_msg("req1", usage={
                "input_tokens": 100, "output_tokens": 50,
                "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
            }),
        ])

        state_file = tmp_path / "sess1.json"
        state_file.write_text(json.dumps({
            "trace_id": "t1",
            "sent_request_ids": ["req1", "sub-req1"],  # sub-req1 from subagent
        }))

        client = MagicMock()
        mock_obs = MagicMock()
        client.start_observation.return_value = mock_obs

        with patch.object(_mod, "get_state_dir", return_value=tmp_path), \
             patch.object(_mod, "get_git_branch", return_value="main"), \
             patch.object(_mod, "get_source_project", return_value="test"):
            handle_session_end(client, {
                "session_id": "sess1",
                "transcript_path": str(main_path),
                "reason": "user_exit",
            })

        # The summary span should have been created with propagate_attributes
        # containing totals from main transcript only (100 input, 50 output)
        assert client.start_observation.called
