ARG BASE_IMAGE=python:3.9-alpine
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

# Install Node packages
COPY ./package.json ./package-lock.json ./
RUN npm install

# Install packages for frontend
COPY ./crispy-forms-govuk /app/crispy-forms-govuk
COPY ./frontend /app/frontend
RUN cd frontend && npm install

# Install Python packages
COPY ./cavl-client /app/cavl-client
COPY ./Pipfile ./Pipfile.lock ./
RUN python --version

RUN pipenv lock --dev -r > requirements.txt \
    && pip install -r requirements.txt

ARG UID=1000
ARG GID=36

RUN addgroup -g $GID django \
    && adduser -s /bin/bash -u $UID -G django -D django

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
