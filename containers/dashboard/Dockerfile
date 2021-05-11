FROM python:3.9

WORKDIR /app

# Copy requirement file
COPY requirements.txt ./

COPY entrypoint.sh ./

# Install all required dependencies
RUN pip install click==7.1.2 rq-dashboard --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --default-timeout=100 && \
    pip install -r requirements.txt  --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --default-timeout=100

CMD ["bash", "entrypoint.sh"]