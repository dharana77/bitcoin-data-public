from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Spark 세션 생성
spark = SparkSession.builder \
    .appName("BronzeToSilver") \
    .master("local[*]") \
    .getOrCreate()

# Bronze 데이터 로드
bronze_df = spark.read.parquet("bronze_data/")

# 데이터 정제 및 가공 (예: 가격이 0 이상인 데이터 필터링)
silver_df = bronze_df.filter(col("price") > 0)

# 중복 제거
silver_df = silver_df.dropDuplicates(["timestamp", "symbol"])

# Silver 계층 저장
silver_df.write.mode("overwrite").parquet("silver_data/")

print("✅ Silver data transformation complete!")
