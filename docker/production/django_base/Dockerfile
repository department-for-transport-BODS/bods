# Base image is only rebuilt by deploy workflows when this file changes.
FROM python:3.14-slim

RUN apt-get update && apt-get install -y g++
RUN pip install pandas==2.3.3 numpy==2.5.4
