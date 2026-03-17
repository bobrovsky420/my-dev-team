from pathlib import Path
from unittest.mock import MagicMock
import pytest
from devteam import cli

def test_parse_spec_from_string_extracts_subject_name():
    content = "Subject: NEW PROJECT: Fancy API\nOwner: Team\n\nBuild a REST API."
    project_name, requirements = cli.parse_spec_from_string(content)
    assert project_name == "Fancy API"
    assert requirements == content.strip()

def test_parse_spec_from_string_defaults_without_subject():
    content = "Owner: Team\n\nBuild a CLI tool."
    project_name, requirements = cli.parse_spec_from_string(content)
    assert project_name == "New Project"
    assert requirements == content.strip()

def test_load_project_spec_reads_file(tmp_path: Path):
    spec_file = tmp_path / "project.txt"
    spec_file.write_text("Subject: NEW PROJECT: Unit Test App\n\nDo work.", encoding="utf-8")
    project_name, requirements = cli.load_project_spec(str(spec_file))
    assert project_name == "Unit Test App"
    assert requirements == "Subject: NEW PROJECT: Unit Test App\n\nDo work."

def test_generate_thread_id_slugifies_name_and_adds_timestamp(monkeypatch):
    class FakeNow:
        def strftime(self, fmt: str) -> str:
            assert fmt == "%Y%m%d_%H%M%S"
            return "20260317_123456"
    class FakeDatetime:
        @staticmethod
        def now():
            return FakeNow()
    monkeypatch.setattr(cli, "datetime", FakeDatetime)
    thread_id = cli.generate_thread_id("My Cool! Project")
    assert thread_id == "my_cool_project_20260317_123456"

def test_my_extensions_returns_expected_extensions(tmp_path: Path):
    extensions = cli.my_extensions(tmp_path)
    assert len(extensions) == 3
    assert extensions[0].__class__.__name__ == "ConsoleLogger"
    assert extensions[1].__class__.__name__ == "WorkspaceSaver"
    assert extensions[2].__class__.__name__ == "HumanInTheLoop"

def test_build_crew_passes_expected_dependencies(monkeypatch):
    captured = {}

    class FakeVirtualCrew:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(cli, "VirtualCrew", FakeVirtualCrew)
    monkeypatch.setattr(cli, "build_agents_from_config", lambda _: ["agent-a", "agent-b"])

    llm_factory = MagicMock(name="llm_factory")
    checkpointer = MagicMock(name="checkpointer")
    ext = [MagicMock(name="extension")]

    crew = cli.build_crew(llm_factory, checkpointer, rpm=7, extensions=ext)

    assert isinstance(crew, FakeVirtualCrew)
    assert captured["manager"].__class__.__name__ == "ProjectManager"
    assert captured["agents"] == ["agent-a", "agent-b"]
    assert captured["extensions"] is ext
    assert captured["llm_factory"] is llm_factory
    assert captured["checkpointer"] is checkpointer
    assert captured["rate_limiter"].rpm_limit == 7


def test_build_crew_without_rpm_disables_rate_limiter(monkeypatch):
    captured = {}

    class FakeVirtualCrew:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(cli, "VirtualCrew", FakeVirtualCrew)
    monkeypatch.setattr(cli, "build_agents_from_config", lambda _: [])

    cli.build_crew(MagicMock(), MagicMock(), rpm=0, extensions=[])

    assert captured["rate_limiter"] is None


@pytest.mark.parametrize(
    "source, expected",
    [
        ("Mixed CASE -- name", "mixed_case_name_20260317_123456"),
        ("  Already__safe  ", "already_safe_20260317_123456"),
    ],
)
def test_generate_thread_id_normalization_variants(monkeypatch, source, expected):
    class FakeNow:
        def strftime(self, fmt: str) -> str:
            return "20260317_123456"
    class FakeDatetime:
        @staticmethod
        def now():
            return FakeNow()
    monkeypatch.setattr(cli, "datetime", FakeDatetime)
    assert cli.generate_thread_id(source) == expected
