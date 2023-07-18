#
#  Makefile
#


include default.mk

SRC = owid tests

# have to customise this because we're using a namespace package
check-typing: .venv
	@echo '==> Checking types'
	.venv/bin/pyright owid tests
