"""把「issue 表单必须合法」变成一条测试 —— 这类错 GitHub 不报，只静默退回空白 issue。

规则来自 GitHub 的 issue-forms 规范里最容易踩的几条：
  · checkboxes 不支持 validations（只有 input / textarea / dropdown 支持）
  · textarea 不支持 maxlength
  · 所有值必须是字符串（YAML 里 `placeholder: 28` 会变成数字）
  · 每个元素必须有 type；input/textarea/dropdown/checkboxes 必须有 attributes.label
  · dropdown 必须有 options 且都是字符串
  · 顶层必须有 name / description / body
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
TPL = ROOT / ".github" / "ISSUE_TEMPLATE"

ALLOWED_ATTRS = {
    "markdown": {"value"},
    "input": {"label", "description", "placeholder", "value"},
    "textarea": {"label", "description", "placeholder", "value", "render"},
    "dropdown": {"label", "description", "options", "multiple", "default"},
    "checkboxes": {"label", "description", "options"},
}
NEEDS_VALIDATIONS = {"input", "textarea", "dropdown"}


def files():
    return sorted(TPL.glob("*.yml"))


def test_have_templates():
    assert files(), "一个 issue 模板都没有"


@pytest.mark.parametrize("path", files(), ids=lambda p: p.name)
def test_template_is_valid(path):
    d = yaml.safe_load(path.read_text(encoding="utf-8"))

    for k in ("name", "description", "body"):
        assert k in d, f"{path.name}: 缺顶层字段 {k}"
    assert isinstance(d["body"], list) and d["body"], f"{path.name}: body 为空"

    for i, b in enumerate(d["body"]):
        t = b.get("type")
        assert t in ALLOWED_ATTRS, f"{path.name}[{i}]: 不认识的 type {t!r}"
        attrs = b.get("attributes") or {}
        extra = set(attrs) - ALLOWED_ATTRS[t]
        assert not extra, f"{path.name}[{i}]: {t} 不支持的字段 {sorted(extra)}"

        if t in ("input", "textarea", "dropdown", "checkboxes"):
            assert attrs.get("label"), f"{path.name}[{i}]: {t} 缺 label"
        if t in ("input", "textarea", "dropdown", "checkboxes"):
            assert b.get("id"), f"{path.name}[{i}]: {t} 缺 id"

        # 最容易踩的一条：checkboxes 写 validations 会让整个表单失效
        if t == "checkboxes":
            assert "validations" not in b, \
                f"{path.name}[{i}]: checkboxes 不能有 validations（GitHub 会静默退回空白 issue）"

        if t == "dropdown":
            opts = attrs.get("options")
            assert isinstance(opts, list) and opts, f"{path.name}[{i}]: dropdown 缺 options"
            assert all(isinstance(o, str) for o in opts), f"{path.name}[{i}]: options 必须全为字符串"

        # 值都必须是字符串（YAML 会把 28 解析成 int）
        for k, v in attrs.items():
            if k == "options":
                continue
            assert isinstance(v, (str, bool)), \
                f"{path.name}[{i}]: {k} 不是字符串（{v!r}）—— 加引号"


def test_rate_form_keeps_three_key_fields():
    """评分表单至少要留：总分、是否用过、一句话理由。少一个就等于没门槛或没可信度。"""
    d = yaml.safe_load((TPL / "rate-part.yml").read_text(encoding="utf-8"))
    labels = [(b.get("attributes") or {}).get("label", "") for b in d["body"]]
    joined = " ".join(labels)
    assert "总分" in joined
    assert "用过" in joined
    assert "一句话理由" in joined
