import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import col, trim


args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "SOURCE_PATH",
        "TARGET_PATH"
    ]
)


sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)


source_path = args["SOURCE_PATH"]
target_path = args["TARGET_PATH"]


print("==========================================")
print("GLUE ETL JOB STARTED")
print("==========================================")
print(f"Source: {source_path}")
print(f"Target: {target_path}")


df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(source_path)
)


print("Input schema:")
df.printSchema()


print(f"Input record count: {df.count()}")


# Clean column names
for column in df.columns:
    clean_name = column.strip().lower()

    if column != clean_name:
        df = df.withColumnRenamed(column, clean_name)


required_columns = [
    "city",
    "state",
    "country"
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:
    raise ValueError(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )


# Clean partition columns
df = (
    df
    .withColumn("city", trim(col("city")))
    .withColumn("state", trim(col("state")))
    .withColumn("country", trim(col("country")))
)


# Remove records where partition columns are empty
df = df.filter(
    col("city").isNotNull()
    & (col("city") != "")
    & col("state").isNotNull()
    & (col("state") != "")
    & col("country").isNotNull()
    & (col("country") != "")
)


print("==========================================")
print("WRITING PARTITIONED PARQUET")
print("==========================================")


(
    df.write
    .mode("overwrite")
    .format("parquet")
    .partitionBy(
        "country",
        "state",
        "city"
    )
    .save(target_path)
)


print("==========================================")
print("GLUE ETL JOB COMPLETED")
print("==========================================")
print("Partitioning:")
print("country / state / city")


job.commit()