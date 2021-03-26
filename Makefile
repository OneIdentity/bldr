
VIRTUALENV ?= .venv
# this will make poetry automatically create .venv
export POETRY_VIRTUALENVS_IN_PROJECT = true
PYCODESTYLE ?= $(VIRTUALENV)/bin/python3 -m pycodestyle
AUTOPEP8 ?= $(VIRTUALENV)/bin/python3 -m autopep8
FLAKE8 ?= $(VIRTUALENV)/bin/python3 -m flake8
MYPY ?= $(VIRTUALENV)/bin/python3 -m mypy


# Auto format by coding style check
.PHONY: autocs
autocs: dev
	$(AUTOPEP8) --in-place --recursive .

# Auto format diff by coding style check
.PHONY: autocs-diff
autocs-diff: dev
	$(AUTOPEP8) --diff --recursive .

# Coding style check
.PHONY: cs
cs: dev
	$(PYCODESTYLE)

.PHONY: lint
lint: dev
	$(FLAKE8)
	$(MYPY)

# Run tests
.PHONY: check
check: dev
	. $(VIRTUALENV)/bin/activate && pytest

# Run tests with specific docker-image
.PHONY: check-docker-image
check-docker-image: dev
	. $(VIRTUALENV)/bin/activate && pytest --docker-image=$(DOCKER_IMAGE)

# Run tests on one selected docker image
.PHONY: quick-check
quick-check:
	. $(VIRTUALENV)/bin/activate && pytest --docker-image=ubuntu:bionic

# Update requirements
.PHONY: update-requirements
update-requirements: $(VIRTUALENV)/bin/python3
	poetry self update
	poetry update

# Create a virtualenv in .venv
$(VIRTUALENV)/bin/python3:
	poetry install --no-dev

# Install development dependencies (for testing) in virtualenv
.PHONY: dev
dev: $(VIRTUALENV)/bin/python3
	poetry install

# Clean directory and delete virtualenv
.PHONY: clean
clean:
	rm -rf dist/
	rm -rf $(VIRTUALENV)

.PHONY: get-version
get-version:
	poetry version -s

.PHONY: bump-version
bump-version:
	poetry version patch
