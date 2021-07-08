#
#  Makefile
#


include default.mk

SRC = owid tests

# have to customise this because we're using a namespace package
check-typing:
	@echo '==> Checking types'
	poetry run mypy owid
	poetry run mypy tests
