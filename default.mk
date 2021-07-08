#
#  default.mk
#

default:
	@echo 'Available commands:'
	@echo
	@echo '  make test      Run all linting and unit tests'
	@echo '  make watch     Run all tests, watching for changes'
	@echo

test-default: lint check-formatting check-typing unittest

lint-default:
	@echo '==> Linting'
	@poetry run flake8

check-formatting-default:
	@echo '==> Checking formatting'
	@poetry run black --check -q .

check-typing-default:
	@echo '==> Checking types'
	@poetry run mypy .

unittest-default:
	@echo '==> Running unit tests'
	@poetry run pytest

format-default:
	@echo '==> Reformatting files'
	@poetry run black -q .

watch-default:
	poetry run watchmedo shell-command -c 'clear; make test' --recursive --drop .

# allow you to override a command, e.g. "watch", but if you do not, then use
# the default
%: %-default
	@true
