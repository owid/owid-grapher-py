#
#  Makefile
#

include default.mk

SRC = owid tests


docs.build: .venv
	@echo '==> Cleaning previous build'
	@rm -rf site/ .cache/
	@mkdir -p .cache
	@echo '==> Building documentation with Zensical'
	@.venv/bin/zensical build -f zensical.toml --clean

docs.serve: .venv
	.venv/bin/zensical serve -f zensical.toml
