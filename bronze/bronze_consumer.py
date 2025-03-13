from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType

KAFKA_TOPIC = "crypto_raw"
BRONZE_PATH = "bronze_data"

# Spark 세션 생성
spark = SparkSession.builder \
    .appName("CryptoRawData") \
    .master("local[*]") \
    .config("spark.sql.streaming.checkpointLocation", "checkpoint/") \
    .getOrCreate()

# JSON 데이터 스키마 정의
schema = StructType([
    StructField("timestamp", TimestampType(), True),
    StructField("symbol", StringType(), True),
    StructField("price", FloatType(), True),
    StructField("volume", FloatType(), True)
])

# Kafka 데이터 읽기
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", KAFKA_TOPIC) \
    .load()

# JSON 파싱
json_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# 데이터를 Bronze 계층에 저장
query = json_df.writeStream \
    .format("parquet") \
    .option("path", BRONZE_PATH) \
    .start()

query.awaitTermination()
