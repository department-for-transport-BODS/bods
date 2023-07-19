ARG BASE_IMAGE=debian:latest

# Step 1 - Build frontend assets
FROM node:19-alpine

WORKDIR /app

COPY ./package.json ./package-lock.json ./
COPY ./transit_odp/frontend/assets ./transit_odp/frontend/assets
COPY ./webpack ./webpack

RUN apk add \
        build-base \
        pkgconfig \
        autoconf \
        automake \
        libtool \
        nasm \
        libffi-dev \
        libxml2-dev \
        libxslt-dev \
        jpeg-dev \
        zlib-dev \
        libpng-dev \
        freetype-dev \
    && npm install \
    && npm run build


# Step 2 - Copy frontend assets and build Django image
FROM ${BASE_IMAGE}

ENV PYTHONUNBUFFERED 1
ENV PATH=$PATH:/app/node_modules/.bin
WORKDIR /app

# Install system packages
RUN ln -s /usr/bin/python3 /usr/bin/python \
    && apk update \
    && apk add \
            --repository http://dl-cdn.alpinelinux.org/alpine/v3.16/main \
            --repository http://dl-cdn.alpinelinux.org/alpine/v3.16/community \
            --no-cache \
            gdal-dev \
            gdal \
            proj-util \
            proj-dev \
            pkgconfig \
            autoconf \
            automake \
            libtool \
            nasm \
            build-base \
            libffi-dev \
            libxml2-dev \
            libxslt-dev \
            libpng-dev \
            freetype-dev \
            jpeg-dev \
            zlib-dev \
            postgresql-dev \
            poppler \
            nodejs \
            npm \
            binutils \
            geos-dev \
    && pip3 install --upgrade pip \
    && pip3 install cython


# Install python packages
# Copy the compiled frontend from step 1 - this ensures production image
# needn't depend on dev tooling
COPY --from=0 /app/transit_odp/frontend/static /app/transit_odp/frontend/static

COPY ./pyproject.toml ./poetry.lock ./
RUN python --version \
    && pip install poetry==1.2.2 \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

# Create non-privileged user
RUN addgroup django \
    && adduser -G django -D django

# Copy all the entry shell scripts to root and prepare them for use
COPY --chown=django:django \
     ./docker/production/django/gunicorn \
     ./docker/production/django/entrypoint \
     ./docker/production/django/start-migrate \
     ./docker/production/django/start-collectstatic \
     ./docker/production/django/celery/worker/start-celeryworker \
     ./docker/production/django/celery/beat/start-celerybeat \
     ./docker/production/django/celery/flower/start-celeryflower \
     /

RUN sed -i 's/\r//' /entrypoint \
    && sed -i 's/\r//' /gunicorn \
    && sed -i 's/\r//' /start-migrate \
    && sed -i 's/\r//' /start-collectstatic \
    && sed -i 's/\r//' /start-celeryworker \
    && sed -i 's/\r//' /start-celerybeat \
    && sed -i 's/\r//' /start-celeryflower \
    && chmod +x /entrypoint /gunicorn /start-migrate /start-collectstatic /start-celeryworker /start-celerybeat /start-celeryflower

# Ensure WORKDIR is owned by django user
RUN chown -R django:django /app
COPY --chown=django:django . /app

USER django

ENTRYPOINT ["/entrypoint"]
