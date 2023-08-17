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
