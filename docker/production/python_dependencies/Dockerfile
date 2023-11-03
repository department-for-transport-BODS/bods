FROM python:3.9-alpine3.16
# This Docker image preinstalls Pandas into the Alpine OS

ENV PYTHONUNBUFFERED 1
ENV PATH=$PATH:/app/node_modules/.bin
WORKDIR /app

# Install system packages
RUN ln -s /usr/bin/python3 /usr/bin/python \
    && apk update \
    && apk --update add --no-cache g++ \
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
    && pip3 install 'cython<3'

# Install python dependencies
COPY ./pyproject.toml ./poetry.lock ./
RUN python --version \
    && pip install poetry==1.2.2 \
    && poetry config virtualenvs.create false \
    && poetry run python -m pip install 'pyproj<3' --no-build-isolation \
    && poetry install --no-dev --no-root
