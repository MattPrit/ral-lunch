FROM openjdk:slim
COPY --from=python:3.11 / /

WORKDIR /app
COPY . /app

RUN pip install .

EXPOSE 8000

CMD ["uvicorn", "ral-lunch.main:app", "--host", "0.0.0.0", "--port", "8000"]