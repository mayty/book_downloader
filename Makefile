

local_install:
	pip install --upgrade pip
	pip install --upgrade uv
	uv sync --active


stylecheck:
	ruff format --diff --check .


style:
	ruff format .


lintcheck:
	ruff check .


lint:
	ruff check --fix --unsafe-fixes .


typecheck:
	mypy .


check: stylecheck lintcheck typecheck
