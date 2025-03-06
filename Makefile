POETRY_VERSION ?= 2.0.1

.PHONY: install-pip
install-pip:
	python -m pip install --upgrade pip

.PHONY: install-poetry
install-poetry:
	curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION}

.PHONY: install-packages
install-packages:
	poetry install --no-root $(opts)

.PHONY: install
install: install-pip install-poetry install-packages

.PHONY: lint
lint:
	poetry run pre-commit run -a
