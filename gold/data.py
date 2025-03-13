gold_df = fact_trades.groupBy("asset_id") \
    .agg(
        avg("price").alias("avg_price"),
        sum("volume").alias("total_volume")
    )

gold_df.write.mode("overwrite").parquet("hdfs://namenode:9000/datalake/gold/aggregated_trades")
