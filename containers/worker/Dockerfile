FROM ubuntu:18.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin

WORKDIR /app

# Copy requirement file
COPY requirements.txt ./

COPY entrypoint.sh ./
COPY requirements.sh ./
COPY script.sh ./

# Install all required dependencies

RUN apt-get update && \
    apt-get install -y software-properties-common tzdata && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update -y && \
    apt-get install -y python3.7 python3-pip python3.7-distutils && \
    ln -s /usr/bin/python3.7 /usr/bin/python && \
    python -m pip install rq watchdog argh pyyaml --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --default-timeout=100 && \
    python -m pip install -r requirements.txt  --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --default-timeout=100

RUN apt-get install -y openjdk-8-jdk default-jre

CMD ["bash", "entrypoint.sh"]