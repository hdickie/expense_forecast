FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "core.ExpenseForecastServer:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
