DJANGO_MANAGE=python sandbox/manage.py
FLAKE=flake8
PYTEST=pytest
PORT=8002
HOST=0.0.0.0

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo
	@echo "  clean-data          -- to clean data (uploaded medias, database, etc..)"
	@echo "  clean-pycache       -- to remove all __pycache__, this is recursive from current directory"
	@echo ""
	@echo "  migrate             -- to apply demo database migrations"
	@echo "  run                 -- to run Django development server for demo"
	@echo ""
	@echo "  flake               -- to launch Flake8 checking"
	@echo "  tests               -- to launch tests using Pytest"
	@echo "  quality             -- to launch Flake8 checking and Pytest"
	@echo

clean-pycache:
	rm -Rf .pytest_cache
	find . -type d -name "__pycache__"|xargs rm -Rf
	find . -name "*\.pyc"|xargs rm -f
.PHONY: clean-pycache

clean-data:
	rm -Rf data
.PHONY: clean-data

migrate:
	mkdir -p data/db
	$(DJANGO_MANAGE) migrate
.PHONY: migrate

run:
	$(DJANGO_MANAGE) runserver ${HOST}:${PORT}
.PHONY: run

flake:
	$(FLAKE) --show-source crispy_forms_govuk
.PHONY: flake

tests:
	$(PYTEST) -vv --exitfirst tests/
.PHONY: tests

quality: tests flake
.PHONY: quality
