
ensure_venv:
ifndef VIRTUAL_ENV
	$(error) "Python virtual env must be active"
endif


local_install: ensure_venv
	pip install --upgrade pip
	pip install --upgrade uv
	uv sync --active


stylecheck: ensure_venv
	ruff format --diff --check .


style: ensure_venv
	ruff format .


lintcheck: ensure_venv
	ruff check .


lint: ensure_venv
	ruff check --fix --unsafe-fixes .


typecheck: ensure_venv
	mypy .


check: stylecheck lintcheck typecheck
