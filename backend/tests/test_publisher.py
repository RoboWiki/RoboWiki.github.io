"""发布器：字段应用、格式保持、GitHub PR 流程。"""
from __future__ import annotations

import base64
import json
import shutil
import tempfile
from pathlib import Path

import httpx
import pytest

from app.publisher import (GitHubPublisher, PublishError, apply_changes,
                           dump_like, find_part_file)


@pytest.fixture()
def tmp_path():
    d = Path(tempfile.mkdtemp(prefix="rw-publisher-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _record():
    return {
        "id": "amass-xt30", "category": "connector", "vendor": "Amass",
        "model": "XT30", "source_tier": "A", "verified": True,
        "last_checked": "2026-10-31",
        "specs": {"positions": 2, "current_rated_A": 20},
    }


def test_apply_changes_specs_and_timestamp():
    out, diff = apply_changes(_record(), {"specs.current_rated_A": 25})
    assert out["specs"]["current_rated_A"] == 25
    assert diff == [{"field": "specs.current_rated_A",
                     "old_value": 20, "new_value": 25}]
    assert out["last_checked"] != "2026-10-31"


def test_apply_changes_rejects_unknown_field():
    with pytest.raises(PublishError):
        apply_changes(_record(), {"specs.minecraft_torque": 1})


def test_dump_like_preserves_crlf_and_indent():
    original = '[\r\n {\r\n  "id": "x"\r\n }\r\n]\r\n'
    text = dump_like(original, [{"id": "x"}])
    assert "\r\n" in text and text.endswith("\r\n")
    assert '\r\n  "id"' in text


def test_find_part_file(tmp_path: Path):
    d = tmp_path / "catalog" / "connector"
    d.mkdir(parents=True)
    (d / "amass.json").write_text(json.dumps([_record()]), encoding="utf-8")
    assert find_part_file(tmp_path, "amass-xt30") == d / "amass.json"
    with pytest.raises(PublishError):
        find_part_file(tmp_path, "nope")


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler),
                        base_url="https://api.github.com", timeout=5)


def test_github_publish_creates_branch_commit_and_pr(tmp_path: Path):
    d = tmp_path / "catalog" / "connector"
    d.mkdir(parents=True)
    (d / "amass.json").write_text(json.dumps([_record()], indent=1), encoding="utf-8")
    current = json.dumps([_record()], indent=1)
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        path = request.url.path
        if request.method == "GET" and path.endswith("/contents/data/catalog/connector/amass.json"):
            ref = request.url.params.get("ref")
            if ref == "proposal/7":
                return httpx.Response(200, json={"sha": "sha-branch",
                                                 "content": base64.b64encode(current.encode()).decode()})
            return httpx.Response(200, json={"sha": "sha-base",
                                             "content": base64.b64encode(current.encode()).decode()})
        if request.method == "GET" and path.endswith("/git/ref/heads/proposal/7"):
            return httpx.Response(404, json={"message": "Not Found"})
        if request.method == "GET" and path.endswith("/git/ref/heads/main"):
            return httpx.Response(200, json={"object": {"sha": "base-commit"}})
        if request.method == "POST" and path.endswith("/git/refs"):
            return httpx.Response(201, json={"ref": "refs/heads/proposal/7"})
        if request.method == "PUT" and path.endswith("/contents/data/catalog/connector/amass.json"):
            body = json.loads(request.content)
            assert body["sha"] == "sha-branch"
            updated = json.loads(base64.b64decode(body["content"]))
            assert updated[0]["specs"]["current_rated_A"] == 25
            return httpx.Response(200, json={"commit": {"sha": "commit-1"}})
        if request.method == "POST" and path.endswith("/pulls"):
            body = json.loads(request.content)
            assert body["head"] == "RoboWiki:proposal/7"
            return httpx.Response(201, json={"html_url": "https://github.com/RoboWiki/RoboWiki/pull/9"})
        return httpx.Response(500, json={"message": f"unexpected {request.method} {path}"})

    pub = GitHubPublisher("token", "RoboWiki/RoboWiki", "main", client=_client(handler))
    result = pub.publish("amass-xt30", {"specs.current_rated_A": 25}, 7,
                         {"note": "样册 p9", "source_url": "https://example.com"},
                         tmp_path)
    assert result["pr_url"].endswith("/pull/9")
    assert result["branch"] == "proposal/7"
    assert result["commit"] == "commit-1"
    assert any(m == "PUT" for m, _ in calls)
    pub.close()
