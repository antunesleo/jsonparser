.PHONY: test install

install:
	uv sync

test:
	uv run pytest

bm:
	python3 benchmark.py
