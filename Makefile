UV ?= uv
export UV_CACHE_DIR ?= $(CURDIR)/.uv-cache
RUN = $(UV) run --frozen

.PHONY: help setup audit test check probe q1 q2 verify extract

help:
	@echo "make setup   安装锁定依赖"
	@echo "make check   输入哈希、数据结构、文档和测试（不改结果）"
	@echo "make probe   复跑 A 题原型与四组合试算，更新 results/probes"
	@echo "make q1      生成 Q1 工作簿、验证报告和数据图
	@echo "make q2      生成 Q2 前 3 h 工作簿、验证报告和数据图""
	@echo "make verify  在临时目录重算并核对已记录证据"
	@echo "make extract 提取题面文本（需要 pdftotext）"

setup:
	$(UV) sync --frozen

audit:
	$(RUN) python code/common/audit.py

test:
	$(RUN) python -m unittest discover -s tests -v

check: audit test
	$(RUN) python code/common/check_project.py

probe:
	$(RUN) python code/common/probes.py --mode all

q1:
	$(RUN) python code/q1/problem1.py

q2:
	$(RUN) python code/q2/problem2.py

verify: check
	$(RUN) python code/common/check_project.py --recompute

extract:
	@mkdir -p results/local
	pdftotext -layout problemA/problemA.pdf results/local/problemA.txt
