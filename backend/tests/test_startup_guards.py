"""启动守卫：生产模式下空数据目录必须拒绝启动。

背景：`seed_catalog` 会把「不在种子里的 Part」全部删除。如果容器把空目录
挂到 `/data`（忘跑 fetch-data-release 或挂载路径写错），启动会先清空目录、
再级联删掉评论——必须在灌库之前拦住。
"""
from __future__ import annotations

import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from app.core.config import settings
from app.core.db import ensure_catalog_present


@pytest.fixture()
def data_dir():
    d = pathlib.Path(tempfile.mkdtemp(prefix="robowiki-guard-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _configure(monkeypatch, *, data_dir: pathlib.Path, auto_create: bool) -> None:
    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "auto_create_tables", auto_create)


def test_empty_catalog_refuses_to_start_in_prod(data_dir, monkeypatch):
    _configure(monkeypatch, data_dir=data_dir, auto_create=False)
    with pytest.raises(RuntimeError, match="catalog"):
        ensure_catalog_present()


def test_missing_catalog_dir_refuses_to_start_in_prod(data_dir, monkeypatch):
    _configure(monkeypatch, data_dir=data_dir / "missing", auto_create=False)
    with pytest.raises(RuntimeError):
        ensure_catalog_present()


def test_present_catalog_passes_in_prod(data_dir, monkeypatch):
    catalog = data_dir / "catalog" / "actuator"
    catalog.mkdir(parents=True)
    (catalog / "dm.json").write_text("[]", encoding="utf-8")
    _configure(monkeypatch, data_dir=data_dir, auto_create=False)
    ensure_catalog_present()


def test_dev_mode_allows_empty_catalog(data_dir, monkeypatch):
    _configure(monkeypatch, data_dir=data_dir, auto_create=True)
    ensure_catalog_present()
