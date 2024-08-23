
run:
  uv run src/main.py

lint:
  uv run ruff check

test:
  uv run pytest