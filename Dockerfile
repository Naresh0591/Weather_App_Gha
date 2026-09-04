FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8000

COPY . .

CMD ["python", "main.py"]
