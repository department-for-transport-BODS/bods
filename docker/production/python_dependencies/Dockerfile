ARG BASE_IMAGE=python:3.10-slim
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

COPY ./pyproject.toml ./poetry.lock ./
RUN pip install poetry==$POETRY_VERSION \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev --no-root
