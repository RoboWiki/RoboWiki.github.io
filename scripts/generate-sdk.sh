#!/usr/bin/env bash
# 从 OpenAPI 生成 clients/sdk/api.d.ts。
#
# 只生成 TypeScript 类型，不生成客户端类、不引入任何运行时依赖：
# App / 小程序 / 脚本都继续用各自的 fetch 封装，只共享这份契约。
#
# 数据源优先级：
#   1. OPENAPI_FILE=/path/openapi.json       （离线 / CI 首选）
#   2. OPENAPI_URL=https://.../openapi.json  （显式指定）
#   3. http://127.0.0.1:8080/api/openapi.json（本机 API）
#   4. https://robowiki.org.cn/api/openapi.json（主域兜底）
#
# 输出路径可用 SDK_OUT 覆盖。脚本可重复执行，输出不含时间戳，内容不变则 diff 为空。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${SDK_OUT:-$ROOT/clients/sdk/api.d.ts}"
LOCAL_URL="${OPENAPI_LOCAL_URL:-http://127.0.0.1:8080/api/openapi.json}"
REMOTE_URL="${OPENAPI_URL:-https://robowiki.org.cn/api/openapi.json}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SOURCE=""
if [[ -n "${OPENAPI_FILE:-}" ]]; then
  if [[ ! -r "$OPENAPI_FILE" ]]; then
    echo "OPENAPI_FILE 不可读：$OPENAPI_FILE" >&2
    exit 1
  fi
  SOURCE="$OPENAPI_FILE"
  echo "openapi: $SOURCE"
elif [[ -n "${OPENAPI_URL:-}" ]]; then
  if ! curl -fsS --max-time 20 "$OPENAPI_URL" -o "$TMP/openapi.json"; then
    echo "无法下载 OpenAPI：$OPENAPI_URL" >&2
    exit 1
  fi
  SOURCE="$TMP/openapi.json"
  echo "openapi: $OPENAPI_URL"
elif curl -fsS --max-time 4 "$LOCAL_URL" -o "$TMP/openapi.json" 2>/dev/null; then
  SOURCE="$TMP/openapi.json"
  echo "openapi: $LOCAL_URL"
elif curl -fsS --max-time 20 "$REMOTE_URL" -o "$TMP/openapi.json"; then
  SOURCE="$TMP/openapi.json"
  echo "openapi: $REMOTE_URL"
else
  echo "拿不到 OpenAPI。启动本机 API、设置 OPENAPI_FILE，或显式给 OPENAPI_URL。" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  # Windows 的 python3 可能是应用商店占位符（能 command -v 到但退出码 49），
  # 所以必须真的跑一次版本检查，而不能只判断命令存在。
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi
if [[ -z "$PYTHON_BIN" ]]; then
  echo "需要 Python 3 来生成类型（也可用 PYTHON=/path/to/python 指定）。" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"

# Git Bash 传 /c/... 给 Windows Python 会解析成 C:\c\...；有 cygpath 时先转原生路径。
native_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$1"
  else
    printf '%s' "$1"
  fi
}
SOURCE_NATIVE="$(native_path "$SOURCE")"
OUT_NATIVE="$(native_path "$OUT")"

PYTHONIOENCODING=utf-8 PYTHONUTF8=1 \
"$PYTHON_BIN" - "$SOURCE_NATIVE" "$OUT_NATIVE" <<'PY'
"""OpenAPI → 单文件 TypeScript 类型。只用标准库，不下载 npm 包。"""
import io
import json
import os
import re
import sys

src, out = sys.argv[1], sys.argv[2]
with io.open(src, encoding="utf-8") as f:
    spec = json.load(f)

# 关键契约缺一不可：本机旧进程（未重建）会缺 /auth/refresh，生成出来是过期 SDK。
REQUIRED_PATHS = (
    "/api/v1/auth/wechat/mini",
    "/api/v1/auth/refresh",
    "/api/v1/notifications",
    "/api/v1/auth/password/set",
    "/api/v1/auth/email/change/request",
    "/api/v1/auth/email/change/confirm",
    "/api/v1/auth/sessions/{session_id}",
    "/api/v1/media",
    "/api/v1/media/{media_id}",
    "/api/v1/ratings/{part_id}",
    "/api/v1/wiki/comments",
)
missing = [p for p in REQUIRED_PATHS if p not in (spec.get("paths") or {})]
if missing:
    raise SystemExit(
        "OpenAPI 缺少必需路径：" + ", ".join(missing)
        + "\nAPI 可能没有重建。用 OPENAPI_FILE 指向当前后端导出的 openapi.json，"
          "或重启本机 API 后重试。"
    )

# FastAPI 里同名 CommentIn 有两个，自动名很长；给它们稳定可读的别名。
ALIASES = {
    "app__api__routes__wiki__CommentIn": "WikiCommentIn",
    "app__schemas__CommentIn": "PostCommentIn",
}
METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def canon(name):
    return ALIASES.get(name, name)


def ref_name(ref):
    return canon(ref.rsplit("/", 1)[-1])


def clean(text):
    return " ".join(str(text).split()).replace("*/", "*\\/")


def doc_lines(text, indent=""):
    if text is None:
        return []
    text = clean(text)
    if not text:
        return []
    return [indent + "/** " + text + " */"]


def prop_key(name):
    return name if IDENT.match(name) else json.dumps(name, ensure_ascii=False)


def literal(value):
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=False)


def needs_parens(t):
    return " | " in t or " & " in t


def ts_type(schema, depth=0):
    """把 OpenAPI schema 转成内联 TS 类型。返回单行字符串。"""
    if schema is None:
        return "unknown"
    if not isinstance(schema, dict):
        return "unknown"
    if "$ref" in schema:
        return ref_name(schema["$ref"])
    if "const" in schema:
        return literal(schema["const"])

    if "allOf" in schema:
        return " & ".join(ts_type(x, depth) for x in schema["allOf"])

    for key in ("oneOf", "anyOf"):
        if key in schema:
            parts = []
            for item in schema[key]:
                t = ts_type(item, depth)
                if item.get("type") == "null":
                    t = "null"
                if t not in parts:
                    parts.append(t)
            return " | ".join(parts)

    if "enum" in schema:
        return " | ".join(literal(v) for v in schema["enum"])

    t = schema.get("type")
    if t == "array":
        item = ts_type(schema.get("items") or {}, depth)
        return ("(" + item + ")[]") if needs_parens(item) else item + "[]"
    if t == "object":
        props = schema.get("properties")
        if props:
            required = set(schema.get("required") or [])
            items = []
            for name, sub in props.items():
                mark = "" if name in required else "?"
                items.append(prop_key(name) + mark + ": " + ts_type(sub, depth + 1))
            return "{ " + "; ".join(items) + " }"
        extra = schema.get("additionalProperties")
        if isinstance(extra, dict):
            return "Record<string, " + ts_type(extra, depth + 1) + ">"
        return "Record<string, unknown>"
    if t == "string":
        return "string"
    if t in ("integer", "number"):
        return "number"
    if t == "boolean":
        return "boolean"
    if t == "null":
        return "null"
    return "unknown"


# ── components.schemas ─────────────────────────────────────────────────────
schemas = spec.get("components", {}).get("schemas", {}) or {}
seen = set()
blocks = []
for original in sorted(schemas, key=lambda n: canon(n)):
    name = canon(original)
    if name in seen:
        raise SystemExit("schema 别名冲突：" + name)
    seen.add(name)
    schema = schemas[original] or {}
    lines = doc_lines(schema.get("description") or schema.get("title"))
    if original != name:
        lines.append("/** OpenAPI 原名：" + original + " */")
    props = schema.get("properties")
    if props and schema.get("type", "object") == "object":
        required = set(schema.get("required") or [])
        lines.append("export interface " + name + " {")
        for prop, sub in props.items():
            lines.extend(doc_lines((sub or {}).get("description"), "  "))
            mark = "" if prop in required else "?"
            lines.append("  " + prop_key(prop) + mark + ": " + ts_type(sub) )
        lines.append("}")
    else:
        lines.append("export type " + name + " = " + ts_type(schema) + ";")
    blocks.append("\n".join(lines))

aliases = []
for original in sorted(ALIASES):
    readable = ALIASES[original]
    aliases.append("/** OpenAPI 原名与可读名等价。 */")
    aliases.append("export type " + original + " = " + readable + ";")


# ── paths → operations ────────────────────────────────────────────────────
def pick_response(op):
    responses = op.get("responses") or {}
    order = [str(x) for x in (200, 201, 202, 203, 204)]
    order += sorted(k for k in responses if k not in order)
    for status in order:
        if status not in responses:
            continue
        body = responses[status] or {}
        content = body.get("content") or {}
        if content:
            media = content.get("application/json") or next(iter(content.values()))
            schema = media.get("schema")
            if schema:
                return ts_type(schema), status
            return "unknown", status
        return ("void" if status == "204" else "unknown"), status
    return "unknown", "200"


def params_type(params, required):
    items = []
    for p in params:
        name = p.get("name") or "param"
        mark = "" if p.get("required") else "?"
        items.append(prop_key(name) + mark + ": " + ts_type(p.get("schema") or {}))
    if not items:
        return None
    return "{ " + "; ".join(items) + " }"


paths = spec.get("paths", {}) or {}
ops = []
for path in sorted(paths):
    methods = paths[path] or {}
    for method in METHODS:
        op = methods.get(method.lower())
        if not op:
            continue
        key = method + " " + path
        lines = doc_lines(op.get("description") or op.get("summary"), "  ")
        if op.get("summary") and op.get("description") and op.get("summary") not in op["description"]:
            lines.extend(doc_lines(op.get("summary"), "  "))
        if op.get("deprecated"):
            lines.append("  /** @deprecated */")
        lines.append("  '" + key + "': {")

        params = op.get("parameters") or []
        py = params_type([p for p in params if p.get("in") == "path"], True)
        qy = params_type([p for p in params if p.get("in") == "query"], False)
        if py:
            lines.append("    path: " + py + ";")
        if qy:
            lines.append("    query: " + qy + ";")

        req = op.get("requestBody") or {}
        content = req.get("content") or {}
        if content:
            media = content.get("application/json") or next(iter(content.values()))
            schema = media.get("schema")
            if schema:
                mark = "" if req.get("required") else "?"
                lines.append("    body" + mark + ": " + ts_type(schema) + ";")

        response, status = pick_response(op)
        lines.append("    response: " + response + ";")
        lines.append("    status: " + status + ";")
        lines.append("  };")
        ops.append("\n".join(lines))

info = spec.get("info") or {}
version = info.get("version") or "0"
title = info.get("title") or "RoboWiki API"

header = [
    "/**",
    " * AUTO-GENERATED by scripts/generate-sdk.sh — do not edit by hand.",
    " *",
    " * " + clean(title) + " " + clean(version) + " OpenAPI",
    " * Regenerate: scripts/generate-sdk.sh",
    " * Offline:    OPENAPI_FILE=/path/openapi.json scripts/generate-sdk.sh",
    " *",
    " * 仅类型，无运行时、无客户端类。认证统一用 Authorization: Bearer <access_token>。",
    " * 未声明 response_model 的接口，response 为 unknown；后端补模型后重新生成即可。",
    " */",
    "",
    "export type ApiMethod = " + " | ".join(json.dumps(m) for m in METHODS) + ";",
    "",
]

body = ["\n\n".join(blocks)] if blocks else []
if aliases:
    body.append("\n".join(aliases))
if ops:
    body.append("export interface ApiOperations {\n" + "\n".join(ops) + "\n}")
body.append("export type ApiOperationKey = keyof ApiOperations;")

text = "\n".join(header) + "\n" + "\n\n".join(body) + "\n"

tmp = out + ".tmp"
with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
os.replace(tmp, out)

print("schemas: %d (aliases %d), operations: %d" % (len(schemas), len(aliases) // 2, len(ops)))
PY

if [[ ! -s "$OUT" ]]; then
  echo "生成结果为空：$OUT" >&2
  exit 1
fi

echo "generated $OUT"
