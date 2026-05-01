FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY src ./src
COPY configs ./configs
COPY scripts ./scripts
COPY docs ./docs

RUN pip install --no-cache-dir -e . -r requirements.txt

ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "-m", "govlexops.etl.pipeline"]
CMD ["--config", "configs/pipeline.yaml"]
