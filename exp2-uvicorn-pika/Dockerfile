FROM python:3.11-slim-bookworm


COPY Pipfile Pipfile.lock ./

RUN pip install pipenv && pipenv install --system --deploy

COPY app/ /app
WORKDIR /app

EXPOSE 8000

CMD ["python", "main.py"]
