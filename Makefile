#
#  Makefile
#


include default.mk

SRC = owid tests

# have to customise this because we're using a namespace package
check-typing:
	@echo '==> Checking types'
	poetry run mypy -p owid
	poetry run mypy tests

watch:
	poetry run watchmedo shell-command -c 'clear; make unittest' --recursive --drop .