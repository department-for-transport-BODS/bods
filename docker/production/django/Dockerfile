ARG BASE_IMAGE=python:3.10-slim

# Step 1 - Build frontend assets
FROM node:20-slim

WORKDIR /app

COPY ./package.json ./yarn.lock ./
COPY ./transit_odp/frontend/assets ./transit_odp/frontend/assets
COPY ./webpack ./webpack

RUN yarn install && yarn build

# Step 2 - Copy frontend assets and build Django image
FROM ${BASE_IMAGE}

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1
ENV PATH=$PATH:/app/node_modules/.bin
WORKDIR /app

RUN echo deb http://ftp.uk.debian.org/debian unstable main contrib non-free >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y \
            libgdal-dev \
            g++ \
            proj-bin \
            pkg-config \
            autoconf \
            automake \
            libtool \
            nasm \
            build-essential \
            libffi-dev \
            libxml2-dev \
            libxslt-dev \
            libpng-dev \
            libfreetype-dev \
            libjpeg-dev \
            zlib1g-dev \
            postgresql \
            libpoppler-dev \
            binutils \
            libgeos-dev \
            && pip3 install --upgrade \
            pip \
            setuptools \
            wheel \
            cython


# Install python packages
# Copy the compiled frontend from step 1 - this ensures production image
# needn't depend on dev tooling
COPY --from=0 /app/transit_odp/frontend/static /app/transit_odp/frontend/static

COPY ./pyproject.toml ./poetry.lock ./
RUN pip install poetry==$POETRY_VERSION \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

# Create non-privileged user
RUN <<EOF
addgroup django
adduser --shell /bin/bash --ingroup django django
EOF

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
COPY --from=0 /app/transit_odp/frontend/static /app/transit_odp/frontend/static

USER django

ENTRYPOINT ["/entrypoint"]
