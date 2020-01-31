import json
import sys
from functools import partial
from operator import attrgetter
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from .models import (
    BitBucketCloudJSONDSL,
    BitBucketServerJSONDSL,
    DangerDSLJSONType,
    DangerDSLJSONTypeSettings,
    GitHubDSL,
    GitJSONDSL,
    GitLabDSL,
)


class Violation(BaseModel):
    message: str
    file_name: Optional[str] = None
    line: Optional[int] = None

    class Config:
        allow_population_by_field_name = True
        fields = {"message": "message", "file_name": "file", "line": "line"}


class DangerResults(BaseModel):
    fails: List[Violation] = []
    warnings: List[Violation] = []
    messages: List[Violation] = []
    markdowns: List[Violation] = []


def serialize_violation(violation: Violation) -> Dict[str, Any]:
    return violation.dict(exclude_none=True, by_alias=True)


def serialize_results(results: DangerResults) -> Dict[str, Any]:
    return results.dict(exclude_none=True, by_alias=True)


def load_dsl() -> DangerDSLJSONType:
    file_url = sys.stdin.read().split("danger://dsl/")[-1]

    with open(file_url, "r") as json_file:
        input_json = json.loads(json_file.read())
        return DangerDSLJSONType(**input_json["danger"])


class Danger:
    def __init__(self):
        if not Danger.dsl:
            Danger.dsl = load_dsl()
        if not Danger.results:
            Danger.results = DangerResults()

    dsl: DangerDSLJSONType = None
    results: DangerResults = None

    @property
    def git(self) -> GitJSONDSL:
        return Danger.dsl.git

    @property
    def github(self) -> GitHubDSL:
        return Danger.dsl.github

    @property
    def bitbucket_cloud(self) -> BitBucketCloudJSONDSL:
        return Danger.dsl.bitbucket_cloud

    @property
    def bitbucket_server(self) -> BitBucketServerJSONDSL:
        return Danger.dsl.bitbucket_server

    @property
    def gitlab(self) -> GitLabDSL:
        return Danger.dsl.gitlab

    @property
    def settings(self) -> DangerDSLJSONTypeSettings:
        return Danger.dsl.settings


def _add_to_results(
    field: Callable[[DangerResults], List[Violation]],
    message: str,
    file_name: Optional[str] = None,
    line: Optional[int] = None,
):
    violation = Violation(message=message, file_name=file_name, line=line)
    field(Danger.results).append(violation)


message = partial(_add_to_results, attrgetter("messages"))
markdown = partial(_add_to_results, attrgetter("markdowns"))
warn = partial(_add_to_results, attrgetter("warnings"))
fail = partial(_add_to_results, attrgetter("fails"))