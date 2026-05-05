.PHONY: test install

install:
	uv sync

test:
	uv run pytest
