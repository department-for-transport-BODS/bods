ARG BASE_IMAGE=python:3.9-alpine

# Multi-stage Build
# Step 1 - Build frontend assets
FROM node:10-alpine

WORKDIR /app

# Install Node packages
COPY ./frontend/package.json ./frontend/package-lock.json ./frontend/
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
    && cd frontend \
    && npm install

# Build assets
COPY ./crispy-forms-govuk ./crispy-forms-govuk
COPY ./frontend ./frontend
RUN cd frontend && npm run build

# Step 2 - Copy frontend assets and build Django image
FROM ${BASE_IMAGE}

ENV PYTHONUNBUFFERED 1
ENV PATH=$PATH:/app/node_modules/.bin
WORKDIR /app

# Install system packages
RUN ln -s /usr/bin/python3 /usr/bin/python \
    && apk update \
    && apk add \
            --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
            --repository http://dl-cdn.alpinelinux.org/alpine/edge/community \
            --no-cache \
            pkgconfig \
            autoconf \
            automake \
            libtool \
            nasm \
            build-base \
            gdal-dev \
            libffi-dev \
            libxml2-dev \
            libxslt-dev \
            libpng-dev \
            freetype-dev \
            jpeg-dev \
            zlib-dev \
            postgresql-dev \
            poppler \
            gdal \
            nodejs \
            npm \
            binutils \
            proj-util \
            proj-dev \
            geos-dev \
    && pip3 install --upgrade pip \
    && pip3 install cython pipenv


# Install python packages
# Copy the compiled frontend from step 1 - this ensures production image needn't depend on dev tooling
COPY --from=0 /app/frontend /app/frontend
COPY ./cavl-client /app/cavl-client
COPY ./crispy-forms-govuk /app/crispy-forms-govuk
COPY ./Pipfile ./Pipfile.lock ./
#RUN pipenv install --deploy --system \
#    && apk del .build-deps
RUN pipenv lock -r > requirements.txt \
    && pip install -r requirements.txt


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
RUN chown django:django /app
COPY --chown=django:django . /app

USER django

ENTRYPOINT ["/entrypoint"]
