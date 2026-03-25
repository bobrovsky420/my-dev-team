from pathlib import Path
import pytest
from devteam.cli.runtime import my_extensions
from devteam.utils import project_spec

def test_parse_spec_from_string_extracts_subject_name():
    content = "Subject: NEW PROJECT: Fancy API\nOwner: Team\n\nBuild a REST API."
    project_name, requirements = project_spec.parse_spec_from_string(content)
    assert project_name == "Fancy API"
    assert requirements == "Build a REST API."

def test_parse_spec_from_string_defaults_without_subject():
    content = "Owner: Team\n\nBuild a CLI tool."
    project_name, requirements = project_spec.parse_spec_from_string(content)
    assert project_name == "New Project"
    assert requirements == "Build a CLI tool."

def test_load_project_spec_reads_file(tmp_path: Path):
    spec_file = tmp_path / "project.txt"
    spec_file.write_text("Subject: NEW PROJECT: Unit Test App\n\nDo work.", encoding="utf-8")
    project_name, requirements = project_spec.load_project_spec(str(spec_file))
    assert project_name == "Unit Test App"
    assert requirements == "Do work."

def test_generate_thread_id_slugifies_name_and_adds_timestamp(monkeypatch):
    class FakeNow:
        def strftime(self, fmt: str) -> str:
            assert fmt == "%Y%m%d_%H%M%S"
            return "20260317_123456"
    class FakeDatetime:
        @staticmethod
        def now():
            return FakeNow()
    monkeypatch.setattr(project_spec, "datetime", FakeDatetime)
    thread_id = project_spec.generate_thread_id("My Cool! Project")
    assert thread_id == "my_cool_project_20260317_123456"

def test_my_extensions_returns_expected_extensions(tmp_path: Path):
    extensions = my_extensions()
    assert len(extensions) == 2
    assert extensions[0].__class__.__name__ == "ConsoleLogger"
    assert extensions[1].__class__.__name__ == "HumanInTheLoop"

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
    monkeypatch.setattr(project_spec, "datetime", FakeDatetime)
    assert project_spec.generate_thread_id(source) == expected
