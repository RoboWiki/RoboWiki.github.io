"""Outbox 发布：把审核通过的提案变成核心仓的 PR。

默认 dry-run；配置 `ROBOWIKI_PUBLISH_MODE=github` + token 后才真的开 PR。
只在 worker 里调用，API 请求路径不会碰 GitHub。
"""
from __future__ import annotations

import base64
import copy
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from .catalog_fields import allowed, split_field
from .core.config import settings


class PublishError(RuntimeError):
    pass


def find_part_file(data_dir: Path, part_id: str) -> Path:
    for path in sorted((Path(data_dir) / "catalog").rglob("*.json")):
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(rows, list) and any(r.get("id") == part_id for r in rows):
            return path
    raise PublishError(f"目录里找不到部件 {part_id}")


def apply_changes(record: dict, changes: dict[str, Any]) -> tuple[dict, list[dict]]:
    out = copy.deepcopy(record)
    specs = dict(out.get("specs") or {})
    diff: list[dict] = []
    for key, value in changes.items():
        if not allowed(key):
            raise PublishError(f"字段不在白名单内：{key}")
        where, field = split_field(key)
        old = specs.get(field) if where == "specs" else out.get(field)
        if old == value:
            continue
        if where == "specs":
            specs[field] = value
        else:
            out[field] = value
        diff.append({"field": key, "old_value": old, "new_value": value})
    if "last_checked" not in changes and diff:
        out["last_checked"] = date.today().isoformat()
    out["specs"] = specs
    return out, diff


def dump_like(original: str, value: Any) -> str:
    """保持核心仓的缩进与换行风格，避免整文件 diff。"""
    newline = "\r\n" if "\r\n" in original else "\n"
    m = re.search(r"\n( +)\S", original.replace("\r\n", "\n"))
    indent = len(m.group(1)) if m else 1
    text = json.dumps(value, ensure_ascii=False, indent=indent)
    if newline != "\n":
        text = text.replace("\n", newline)
    if original.endswith(("\n", "\r\n")):
        text += newline
    return text


class GitHubPublisher:
    def __init__(self, token: str, repo: str, base: str = "main",
                 client: httpx.Client | None = None):
        self.repo = repo
        self.base = base
        self._client = client or httpx.Client(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "RoboWiki-worker",
            },
            timeout=20,
        )

    def close(self) -> None:
        self._client.close()

    def _req(self, method: str, path: str, **kw) -> httpx.Response:
        r = self._client.request(method, path, **kw)
        if r.status_code >= 400:
            raise PublishError(f"GitHub {method} {path} -> {r.status_code}: {r.text[:300]}")
        return r

    def _ensure_branch(self, branch: str) -> None:
        r = self._client.get(f"/repos/{self.repo}/git/ref/heads/{branch}")
        if r.status_code == 200:
            return
        if r.status_code != 404:
            raise PublishError(f"读取分支失败：{r.status_code} {r.text[:200]}")
        base = self._req("GET", f"/repos/{self.repo}/git/ref/heads/{self.base}")
        sha = base.json()["object"]["sha"]
        r = self._client.post(f"/repos/{self.repo}/git/refs",
                              json={"ref": f"refs/heads/{branch}", "sha": sha})
        if r.status_code not in (201, 422):
            raise PublishError(f"创建分支失败：{r.status_code} {r.text[:200]}")

    def _get_file(self, path: str, ref: str) -> tuple[dict, str]:
        r = self._client.get(f"/repos/{self.repo}/contents/{path}", params={"ref": ref})
        if r.status_code == 404:
            raise PublishError(f"核心仓没有文件 {path}")
        if r.status_code >= 400:
            raise PublishError(f"读取文件失败：{r.status_code} {r.text[:200]}")
        d = r.json()
        return d, base64.b64decode(d["content"]).decode("utf-8")

    def _put_file(self, path: str, text: str, branch: str, message: str,
                  sha: str | None) -> dict:
        body = {"message": message, "branch": branch,
                "content": base64.b64encode(text.encode("utf-8")).decode()}
        if sha:
            body["sha"] = sha
        r = self._client.put(f"/repos/{self.repo}/contents/{path}", json=body)
        if r.status_code not in (200, 201):
            raise PublishError(f"提交文件失败：{r.status_code} {r.text[:200]}")
        return r.json()

    def _open_pr(self, branch: str, title: str, body: str) -> str:
        owner = self.repo.split("/")[0]
        r = self._client.post(f"/repos/{self.repo}/pulls",
                              json={"title": title, "head": f"{owner}:{branch}",
                                    "base": self.base, "body": body})
        if r.status_code == 201:
            return r.json()["html_url"]
        if r.status_code == 422:
            owner = self.repo.split("/")[0]
            q = self._client.get(f"/repos/{self.repo}/pulls",
                                 params={"head": f"{owner}:{branch}", "state": "open"})
            if q.status_code == 200 and q.json():
                return q.json()[0]["html_url"]
        raise PublishError(f"创建 PR 失败：{r.status_code} {r.text[:300]}")

    def publish(self, part_id: str, changes: dict, submission_id: int | None,
                evidence: dict, data_dir: Path) -> dict:
        local = find_part_file(data_dir, part_id)
        repo_path = "data/" + local.relative_to(Path(data_dir)).as_posix()
        branch = f"proposal/{submission_id}" if submission_id else f"proposal/{part_id}"

        _, current = self._get_file(repo_path, self.base)
        rows = json.loads(current)
        index = next((i for i, r in enumerate(rows) if r.get("id") == part_id), None)
        if index is None:
            raise PublishError(f"{repo_path} 里找不到 {part_id}")
        updated, diff = apply_changes(rows[index], changes)
        if not diff:
            return {"skipped": True, "reason": "已经是目标值", "path": repo_path}
        rows[index] = updated
        text = dump_like(current, rows)

        self._ensure_branch(branch)
        branch_info, at_branch = self._get_file(repo_path, branch)
        if at_branch == text:
            return {"skipped": True, "reason": "分支上已经是目标值", "branch": branch}

        note = (evidence or {}).get("note") or ""
        source = (evidence or {}).get("source_url") or ""
        fields = ", ".join(x["field"] for x in diff)
        commit = self._put_file(
            repo_path, text, branch,
            f"data: 提案 #{submission_id or '?'} {part_id} — {fields}",
            branch_info["sha"])
        title = f"data: 提案 #{submission_id or '?'} {part_id}"
        body = "\n".join(x for x in [
            f"自动生成自 RoboWiki 审核队列（提案 #{submission_id or '?'}）。",
            "", f"- 部件：`{part_id}`", f"- 文件：`{repo_path}`",
            f"- 字段：{fields}", f"- 依据：{note}" if note else "",
            f"- 来源：{source}" if source else "",
            "", "审核通过只代表允许进入发布流程；合并与 `data-v*` release 后目录才会更新。",
        ] if x is not None)
        pr = self._open_pr(branch, title, body)
        return {"pr_url": pr, "branch": branch, "path": repo_path,
                "commit": commit.get("commit", {}).get("sha"), "diff": diff}


def publish_job(job, data_dir: Path) -> dict:
    """按配置选择发布方式；默认 dry-run 写本地产物。"""
    if settings.publish_mode == "github":
        if not settings.github_token:
            raise PublishError("PUBLISH_MODE=github 但未配置 ROBOWIKI_GITHUB_TOKEN")
        payload = job.payload or {}
        publisher = GitHubPublisher(settings.github_token, settings.core_repo,
                                    settings.core_branch)
        try:
            return publisher.publish(
                payload.get("target_id"), payload.get("changes") or {},
                job.submission_id, payload.get("evidence") or {}, data_dir)
        finally:
            publisher.close()

    out_dir = Path(os.environ.get("ROBOWIKI_OUTBOX_DIR", "var/outbox"))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"submission-{job.submission_id or job.id}.json"
    path.write_text(json.dumps({
        "outbox_id": job.id, "submission_id": job.submission_id,
        "action": job.action, "payload": job.payload,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"dry_run": True, "file": path.name}
