#
#  Makefile
#

include default.mk

unittest:
	@echo '==> Running unit tests'
	@PYTHONPATH=. poetry run pytest

check-typing:
	@echo '==> Checking types'
	@pyright
