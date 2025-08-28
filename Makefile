# Minimal Playwright setup (Python version)

.PHONY: dev-install playwright-install

dev-install:
	python -m pip install -U pip
	pip install -e .[dev]

playwright-install:
	python -m playwright install
