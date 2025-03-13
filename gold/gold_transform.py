from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, max, min, count, sum, date_format

# Spark 세션 생성
spark = SparkSession.builder \
    .appName("SilverToGold") \
    .master("local[*]") \
    .getOrCreate()

# Silver 데이터 로드
silver_df = spark.read.parquet("silver_data/")

# 시간 차원 테이블 생성 (dim_time)
dim_time = silver_df.select(
    col("timestamp"),
    date_format("timestamp", "yyyy-MM-dd").alias("date"),
    date_format("timestamp", "HH").alias("hour")
).dropDuplicates()

# 거래소 심볼 차원 테이블 생성 (dim_symbol)
dim_symbol = silver_df.select("symbol").dropDuplicates()

# 거래 데이터 집계 (fact_trades)
fact_trades = silver_df.groupBy("timestamp", "symbol") \
    .agg(
        avg("price").alias("avg_price"),
        max("price").alias("max_price"),
        min("price").alias("min_price"),
        sum("volume").alias("total_volume"),
        count("*").alias("trade_count")
    )

# 데이터 저장 (Parquet)
dim_time.write.mode("overwrite").parquet("gold_data/dim_time/")
dim_symbol.write.mode("overwrite").parquet("gold_data/dim_symbol/")
fact_trades.write.mode("overwrite").parquet("gold_data/fact_trades/")

print("Gold data transformation complete.")
