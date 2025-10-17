#Construir o seu serviço de API

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "app:app"]
