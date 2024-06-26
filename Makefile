.PHONY: %

up:
	docker compose up

up-bg:
	docker compose up -d

stop:
	docker compose down

kill:
	docker compose kill

logs-%:
	docker logs -f bods-$*-1

restart-%:
	docker restart bods-$*-1

COMMAND ?= sh

exec-%:
	docker exec -it bods-$*-1 $(COMMAND)

test-%:
	@{ \
		if [ $$(docker exec -it bods-django-1 sh -c "test -d transit_odp/$*/tests && echo 'exists'") ]; then \
			docker exec -it bods-django-1 pytest --no-cov --disable-warnings transit_odp/$*/tests/$(TEST); \
		else \
			docker exec -it bods-django-1 pytest --no-cov --disable-warnings transit_odp/$*/tests.py$(TEST); \
		fi \
	}

all-tests:
	docker exec -it bods-django-1 pytest --no-cov --disable-warnings

lint:
	docker exec -it bods-django-1 black --check --config .black.toml .

lint-fix:
	docker exec -it bods-django-1 black --config .black.toml .

local-db-backup:
	docker exec -t bods-postgres-1 pg_dump -U transit_odp -d transit_odp > db_backup.sql

local-db-restore:
	docker exec -i bods-postgres-1 psql -U transit_odp -d transit_odp < db_backup.sql
	rm -rf db_backup.sql

djlint:
	djlint ./transit_odp --reformat | sed 's/^/[$@]\t/'

static:
	webpack --config webpack/dev.js | sed 's/^/[$@]\t/'

django:
	python -m manage runserver 0.0.0.0:8001 | sed 's/^/[$@]\t/'

beat:
	celery -A transit_odp.taskapp beat -l INFO --scheduler=django_celery_beat.schedulers:DatabaseScheduler | sed 's/^/[$@]\t/'

flower:
	celery --app=transit_odp.taskapp --broker=\"redis://localhost:6379/0\" flower --basic_auth=\"admin:admin\" | sed 's/^/[$@]\t/'

worker:
	hupper -m celery -A transit_odp.taskapp worker --pool threads -l INFO | sed 's/^/[$@]\t/'

redis:
	redis-server | sed 's/^/[$@]\t/'

mailhog:
	mailhog | sed 's/^/[$@]\t/'

migrate:
	python -m manage migrate | sed 's/^/[$@]\t/'

test:
	pytest -vv --junitxml=junit_report.xml || [ $? = 1 ] | sed 's/^/[$@]\t/'

serve: redis mailhog migrate django beat flower worker static
