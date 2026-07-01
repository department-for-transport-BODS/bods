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
	docker exec -it bods-django-1 djlint . --lint

lint-fix:
	docker exec -it bods-django-1 black --config .black.toml .
	docker exec -it bods-django-1 djlint . --reformat


local-db-backup:
	docker exec -t bods-postgres-1 pg_dump -U transit_odp -d transit_odp > db_backup.sql

local-db-restore:
	docker exec -i bods-postgres-1 psql -U transit_odp -d transit_odp < db_backup.sql
	rm -rf db_backup.sql

RUN_TASK_MODULE ?= otc
RUN_TASK_NAME ?= task_refresh_weca_data
# Example: RUN_TASK_KWARGS="keyword='Value'"
RUN_TASK_KWARGS ?=

run-task:
	docker exec -i bods-django-1 python manage.py shell -c \
	"from transit_odp.${RUN_TASK_MODULE}.tasks import $(RUN_TASK_NAME); \
	$(RUN_TASK_NAME).run($(RUN_TASK_KWARGS))"

print-env:
	docker exec -i bods-django-1 printenv
