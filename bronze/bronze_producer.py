from fastapi import FastAPI
import requests
from kafka import KafkaProducer
import json

app = FastAPI()
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

EXCHANGE_API_URL = "https://api.exchange.com/data"


@app.get("/fetch-data")
def fetch_data(start_date: str, end_date: str):
    response = requests.get(EXCHANGE_API_URL)
    if response.status_code == 200:
        data = response.json()
        producer.send("crypto_raw", data)
        return {"message": "Data sent to Kafka"}

    else:
        return {"error": "Failed to fetch data"}
