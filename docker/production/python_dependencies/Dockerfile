ARG BASE_IMAGE=python:3.14-slim
FROM ${BASE_IMAGE}

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.4.3
ENV PATH=$PATH:/app/node_modules/.bin
WORKDIR /app

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

COPY ./pyproject.toml ./poetry.lock ./
RUN python -m venv /opt/poetry \
    && /opt/poetry/bin/pip install poetry==$POETRY_VERSION \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-root
