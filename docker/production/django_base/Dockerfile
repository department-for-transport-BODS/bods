FROM python:3.10-slim
# This Docker image preinstalls Pandas into the Alpine OS

RUN echo deb http://ftp.uk.debian.org/debian unstable main contrib non-free >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y g++
RUN pip install pandas==2.1.4 numpy==1.26.2
