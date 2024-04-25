FROM python:3.11-slim

WORKDIR /opt/app
RUN groupadd -r web && useradd -d /opt/app -g web web \
    && chown web:web -R /opt/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE 'config.settings'

COPY requirements.txt requirements.txt

RUN  pip install --upgrade pip \
     && pip install -r requirements.txt

COPY . .

USER web

CMD ["python", "start_process.py"]
