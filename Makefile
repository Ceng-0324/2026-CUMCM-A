UV ?= uv
export UV_CACHE_DIR ?= $(CURDIR)/.uv-cache
RUN = $(UV) run --frozen

.PHONY: help setup audit test check probe verify extract

help:
	@echo "make setup   安装锁定依赖"
	@echo "make check   输入哈希、数据结构、文档和测试（不改结果）"
	@echo "make probe   复跑 A 题原型与四组合试算，更新 results/probes"
	@echo "make verify  在临时目录重算并核对已记录证据"
	@echo "make extract 提取题面文本（需要 pdftotext）"

setup:
	$(UV) sync --frozen

audit:
	$(RUN) python code/audit.py

test:
	$(RUN) python -m unittest discover -s tests -v

check: audit test
	$(RUN) python code/check_project.py

probe:
	$(RUN) python code/probes.py --mode all

verify: check
	$(RUN) python code/check_project.py --recompute

extract:
	@mkdir -p results/local
	pdftotext -layout problemA/problemA.pdf results/local/problemA.txt
