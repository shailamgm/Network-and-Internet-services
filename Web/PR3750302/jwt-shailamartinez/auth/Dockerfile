FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.3 "pyjwt[crypto]==2.9.0" gunicorn==23.0.0
COPY app.py ./
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
USER 10001
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "app:app"]
