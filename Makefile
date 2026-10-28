# RoboSelect —— 常用命令
#
# 一条命令跑完构建链：validate + build
# 外部贡献者最常用的三条：make validate / make build / make test

PY ?= python
NPM ?= npm

.PHONY: help validate build test site serve clean

help:
	@echo "make validate   数据闸门（PR 与 CI 的必过关）"
	@echo "make build      生成站点内容与静态产物（catalog.json 等）"
	@echo "make site       构建 VitePress 静态站点"
	@echo "make test       pipeline + backend 全部测试"
	@echo "make serve      本地起站点热更（5174）"
	@echo "make clean      清掉生成物（wiki/docs/parts 与 public/catalog.json）"

validate:
	$(PY) -m pipeline validate

build:
	$(PY) -m pipeline build

test:
	$(PY) -m pytest

site: build
	cd wiki && $(NPM) run build

serve:
	cd wiki && $(NPM) run dev

# 只删「由 pipeline 生成」的东西，不碰 data/ 与图片
clean:
	rm -rf wiki/docs/parts wiki/docs/index.md wiki/docs/semantics.md wiki/docs/sources.md
	rm -f wiki/docs/public/catalog.json wiki/docs/.vitepress/sidebar.json
