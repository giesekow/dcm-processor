FROM python:3.7

WORKDIR /app

# Copy requirement file
COPY requirements.txt ./

COPY entrypoint.sh ./

# Install all required dependencies
RUN pip install redis rq flask requests python-dotenv --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --default-timeout=100 && \
    pip install -r requirements.txt --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --default-timeout=100

COPY . .

ENV FLASK_APP="app.py"

CMD ["bash", "entrypoint.sh"]