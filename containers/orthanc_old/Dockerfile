FROM jodogne/orthanc-plugins:1.6.1

RUN apt-get update
RUN apt-get install -y python3-pip

RUN pip3 install requests numpy --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --default-timeout=100