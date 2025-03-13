from pyspark.sql.functions import col
from pyspark.sql import SparkSession

spark = SparkSession

spark = SparkSession.builder \
        .appName("CryptoRawData") \
        .getOrCreate()

df = spark.read.parquet("hdfs://namenode:9000/datalake/bronze/crypto")

dim_assets = df.select("symbol").distinct() \
    .withColumnRenamed("symbol", "asset_id")

dim_assets.wrtie.mode("overwrite").parquet("hdfs://namenode:9000/datalake.silver/dim_assets")


fact_trades = df.select("timestamp", "symbol", "price", "volumne")\
    .withColumnRenamed("symbol", "asset_id")

fact_trades.write.mode("overwrite").parquet("hdfs://namenode:9000/datalake/silver/fact_trades")
