ARG BASE_IMAGE=python:3.10-slim
FROM ${BASE_IMAGE}

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.0

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
            nodejs \
            npm \
            binutils \
            libgeos-dev \
    && pip3 install --upgrade pip setuptools wheel cython


# Update C env vars so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

COPY ./pyproject.toml ./poetry.lock ./package.json ./yarn.lock ./

RUN python --version \
    && npm install -g yarn@latest \
    && yarn set version stable && yarn install \
    && pip install poetry==$POETRY_VERSION \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi -vvv

# ARG UID=1001
# ARG GID=36

RUN <<EOF
addgroup django
adduser --shell /bin/bash --ingroup django django
EOF

# Copy all the entry shell scripts to root and prepare them for use
COPY ./docker/production/django/entrypoint \
     ./docker/production/django/start-migrate \
     ./docker/production/django/start-collectstatic \
     ./docker/local/django/start \
     ./docker/local/django/celery/worker/start-celeryworker \
     ./docker/local/django/celery/beat/start-celerybeat \
     ./docker/local/django/celery/flower/start-celeryflower \
      /

RUN chown django:django /entrypoint /start /start-migrate /start-collectstatic /start-celeryworker /start-celerybeat /start-celeryflower

RUN sed -i 's/\r//' /entrypoint \
    && sed -i 's/\r//' /start \
    && sed -i 's/\r//' /start-migrate \
    && sed -i 's/\r//' /start-collectstatic \
    && sed -i 's/\r//' /start-celeryworker \
    && sed -i 's/\r//' /start-celerybeat \
    && sed -i 's/\r//' /start-celeryflower \
    && chmod +x /entrypoint /start /start-migrate /start-collectstatic /start-celeryworker /start-celerybeat /start-celeryflower

# NOTE - copying the src into the image is redundant in development as we bind mount the project directory
# but is required for the GitLab CI pipeline to run tests. We could work around this by adding the bind mount in the CI

# Ensure WORKDIR is owned by django user
RUN chown django:django /app

#COPY --chown=django:django . /app
COPY . /app
RUN chown django:django /app

USER django

ENTRYPOINT ["/entrypoint"]
