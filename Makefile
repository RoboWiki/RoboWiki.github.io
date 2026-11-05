# RoboWiki —— 常用命令
#
# 一条命令跑完构建链：validate + build（pipeline 生成 JSON 并导出给 Astro）
# 外部贡献者最常用的：make validate / make build / make test / make web

PY ?= python
PNPM ?= pnpm

.PHONY: help data validate build test web app serve clean

help:
	@echo "make data       下载 data.lock.json 锁定的核心仓数据")
	@echo "make validate   数据闸门（PR 与 CI 的必过关）"
	@echo "make build      生成 JSON 并导出到 apps/web（pipeline build）"
	@echo "make web        构建 Astro 根站（apps/web/dist）"
	@echo "make app        构建 Taro H5（apps/app/dist/h5）"
	@echo "make test       pipeline + backend 全部测试"
	@echo "make serve      本地起 Astro 开发服务器"
	@echo "make clean      清掉 pipeline 生成物与前端构建缓存"

data:
	bash scripts/fetch-data-release.sh

validate:
	$(PY) -m pipeline validate

build:
	$(PY) -m pipeline build

test:
	$(PY) -m pytest

web: build
	$(PNPM) --filter @robowiki/web build

app:
	APP_BASE=/app/ $(PNPM) --filter @robowiki/app build:h5

serve:
	$(PNPM) --filter @robowiki/web dev

# 只删「由 pipeline 生成」的东西，不碰数据与发布物
clean:
	rm -rf apps/web/src/data apps/web/public/parts apps/web/public/share
	rm -f apps/web/public/*.json apps/web/public/llms.txt
	rm -rf apps/web/dist apps/app/dist
