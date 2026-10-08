FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser
COPY --chown=10001:10001 app.py ./

USER 10001:10001
EXPOSE 8000
CMD ["python", "app.py"]
