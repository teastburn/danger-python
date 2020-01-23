import sys
from io import StringIO
from typing import Dict
from unittest import mock

import pytest

from danger_python.danger import (
    Danger,
    DangerResults,
    Violation,
    fail,
    load_dsl,
    markdown,
    message,
    serialize_results,
    serialize_violation,
    warn,
)
from tests.fixtures.danger import danger_input_file_fixture


def test_violation_is_correctly_serialized():
    """
    Test that Violation model is correctly serialized.
    """
    violation = Violation(message="Title", file_name="file.py", line=28)

    json = serialize_violation(violation)

    assert json == {"message": "Title", "file": "file.py", "line": 28}


def test_violation_is_correctly_serialized_with_optional_types():
    """
    Test that Violation model is correctly serialized with optional types.
    """
    violation = Violation(message="Message")

    json = serialize_violation(violation)

    assert json == {"message": "Message"}


def test_results_are_correctly_serialized():
    """
    Test that DangerResults model is correctly serialized.
    """
    results = DangerResults(
        fails=[Violation(message="Fail")],
        warnings=[Violation(message="Warning", file_name="warning.py", line=99)],
        messages=[Violation(message="Message")],
        markdowns=[Violation(message="Markdown")],
    )

    json = serialize_results(results)

    assert json == {
        "fails": [{"message": "Fail"},],
        "warnings": [{"message": "Warning", "file": "warning.py", "line": 99},],
        "messages": [{"message": "Message"},],
        "markdowns": [{"message": "Markdown"}],
    }


def __load_dsl_files() -> Dict[str, str]:
    danger_dsl_json = danger_input_file_fixture(
        modified_files=["a.py"], created_files=["b.py"], deleted_files=["c.py"]
    )
    return {"/var/folders/zx/danger-dsl.json": danger_dsl_json}


@pytest.mark.parametrize("stdin_str", ["danger://dsl//var/folders/zx/danger-dsl.json"])
@pytest.mark.parametrize("files", [__load_dsl_files()])
@pytest.mark.usefixtures("stdin", "filesystem")
def test_load_dsl_method_works():
    """
    Test that loading DSL from file works.
    """
    dsl = load_dsl()

    assert dsl
    assert dsl.git.modified_files == ["a.py"]
    assert dsl.git.created_files == ["b.py"]
    assert dsl.git.deleted_files == ["c.py"]


@pytest.mark.parametrize("modified_files", [["first_file.py", "module/second_file.py"]])
@pytest.mark.parametrize("created_files", [["new_file.py"]])
@pytest.mark.parametrize("deleted_files", [["file_to_delete.py"]])
def test_danger_parses_input(danger):
    """
    Test that Danger parses JSON file with the URL read from the standard input.
    """
    assert danger.git.modified_files == ["first_file.py", "module/second_file.py"]
    assert danger.git.created_files == ["new_file.py"]
    assert danger.git.deleted_files == ["file_to_delete.py"]
    assert danger.github.pr.title == "Evaluate RHS of binding/assignment pattern first"


@pytest.mark.usefixtures("danger")
def test_message_method_appends_message_to_results():
    """
    Test that message method appends a message to results.
    """
    message("Hey, this is great!")
    message("This file is too big", "big_file.py", 2049)

    assert len(Danger.results.messages) == 2
    assert Danger.results.messages[0] == Violation(message="Hey, this is great!")
    assert Danger.results.messages[1] == Violation(
        message="This file is too big", file_name="big_file.py", line=2049
    )


@pytest.mark.usefixtures("danger")
def test_markdown_method_appends_markdown_to_results():
    """
    Test that markdown method appends a message to results.
    """
    markdown("Markdown #1")
    markdown("Markdown #2", "README.md", 1)

    assert len(Danger.results.markdowns) == 2
    assert Danger.results.markdowns[0] == Violation(message="Markdown #1")
    assert Danger.results.markdowns[1] == Violation(
        message="Markdown #2", file_name="README.md", line=1
    )


@pytest.mark.usefixtures("danger")
def test_warn_method_appends_warning_to_results():
    """
    Test that warn method appends a warning to results.
    """
    warn("Possible memory leak")
    warn("This method is deprecated", "deprecated.py", 29)

    assert len(Danger.results.warnings) == 2
    assert Danger.results.warnings[0] == Violation(message="Possible memory leak")
    assert Danger.results.warnings[1] == Violation(
        message="This method is deprecated", file_name="deprecated.py", line=29
    )


@pytest.mark.usefixtures("danger")
def test_fail_method_appends_failure_to_results():
    """
    Test that fail method appends a failure to results.
    """
    fail("Division by zero")
    fail("This crashes due to invalid shoe size", "shoes.py", 99)

    assert len(Danger.results.fails) == 2
    assert Danger.results.fails[0] == Violation(message="Division by zero")
    assert Danger.results.fails[1] == Violation(
        message="This crashes due to invalid shoe size", file_name="shoes.py", line=99
    )
