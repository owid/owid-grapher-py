#
#  default.mk
#

SRC = src test

default:
	@echo 'Available commands:'
	@echo
	@echo '  make test      Run all linting and unit tests'
	@echo '  make watch     Run all tests, watching for changes'
	@echo

# check formatting before lint, since an autoformat might fix linting issues
test-default: check-formatting lint check-typing unittest

.venv: pyproject.toml poetry.lock poetry.toml
	poetry install
	touch $@

lint-default: .venv
	@echo '==> Linting'
	.venv/bin/flake8 $(SRC)

check-formatting-default: .venv
	@echo '==> Checking formatting'
	.venv/bin/black --check $(SRC)

check-typing-default: .venv
	@echo '==> Checking types'
	PYTHONPATH=. .venv/bin/mypy $(SRC)

unittest-default: .venv
	@echo '==> Running unit tests'
	@PYTHONPATH=. .venv/bin/pytest

format-default: .venv
	@echo '==> Reformatting files'
	.venv/bin/black $(SRC)

watch-default: .venv
	.venv/bin/watchmedo shell-command -c 'clear; make test' --recursive --drop .

# allow you to override a command, e.g. "watch", but if you do not, then use
# the default
%: %-default
	@true
