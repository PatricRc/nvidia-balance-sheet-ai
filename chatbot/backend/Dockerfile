# Build from the repository root so the measure catalog (dax/) and concept map ship with the image:
#   docker build -f chatbot/backend/Dockerfile -t nvidia-analyst .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY chatbot/backend/requirements.txt chatbot/backend/requirements.txt
RUN pip install --no-cache-dir -r chatbot/backend/requirements.txt

# Retrieval catalog sources (read at startup) + the service code
COPY dax ./dax
COPY fabric/notebooks/nb_bronze_silver_gold_sec_edgar.ipynb ./fabric/notebooks/
COPY chatbot/backend/app ./chatbot/backend/app

RUN useradd --uid 10001 --no-create-home appuser
USER 10001
WORKDIR /srv/chatbot/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
