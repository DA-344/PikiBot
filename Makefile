PYTHON := python
.PHONY: help i18n-compile

## Usage: help
## Show available commands and their usage.
help:
	$(PYTHON) scripts/help.py


## Usage: i18n-compile LOCALE_DIR=<path> DOMAINS=<domain1>,<domain2>,...
## Compiles all translations catalogs and domains in the specified LOCALE_DIR. DOMAINS is optional and may be specified as a
## comma-separated list of domains to compile.
i18n-compile:
	$(PYTHON) scripts/i18n/compile.py \
		--locale-dir "$(LOCALE_DIR)" \
		--domains "$(DOMAINS)"
