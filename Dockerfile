FROM python:3-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "./httpServer2.py"]