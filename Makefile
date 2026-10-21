### Defensive settings for make:
#     https://tech.davis-hansson.com/p/make/
SHELL:=bash
.ONESHELL:
.SHELLFLAGS:=-xeu -o pipefail -O inherit_errexit -c
.SILENT:
.DELETE_ON_ERROR:
MAKEFLAGS+=--warn-undefined-variables
MAKEFLAGS+=--no-builtin-rules

# We like colors
# From: https://coderwall.com/p/izxssa/colored-makefile-for-golang-projects
RED=`tput setaf 1`
GREEN=`tput setaf 2`
RESET=`tput sgr0`
YELLOW=`tput setaf 3`

PACKAGE_NAME=collective.sentry

# Python checks
UV?=uv

# installed?
ifeq (, $(shell which $(UV) ))
  $(error "UV=$(UV) not found in $(PATH)")
endif

# Release tooling, matching the pins used by the ploud backend. Everything runs
# in an ephemeral uvx environment, so no local virtualenv is required. The
# changelog is CHANGES.txt, maintained by hand: zest.releaser dates the
# "(unreleased)" heading on release and opens the next one afterwards.
RELEASE_TOOLING=--from zest.releaser[recommended]==9.9.1

# Environment variables to be exported
export PYTHONWARNINGS := ignore

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'
.PHONY: help
help: ## This help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: release
release: ## Release a new version (settings in setup.cfg [zest.releaser])
	@echo "$(GREEN)==> Releasing $(PACKAGE_NAME)$(RESET)"
	@uvx $(RELEASE_TOOLING) fullrelease
