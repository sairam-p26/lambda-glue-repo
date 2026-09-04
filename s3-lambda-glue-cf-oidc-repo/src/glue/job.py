import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext


args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "SOURCE_BUCKET",
        "SOURCE_KEY",
        "OUTPUT_PATH",
    ],
)

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)

source_path = f"s3://{args['SOURCE_BUCKET']}/{args['SOURCE_KEY']}"

print(f"Reading: {source_path}")

df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(source_path)
)

required = {"city", "state", "country"}
actual = {c.lower() for c in df.columns}

missing = required - actual

if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

# Normalize column names so partition columns are predictable.
rename_map = {}
for c in df.columns:
    normalized = c.strip().lower()
    if normalized != c:
        rename_map[c] = normalized

for old, new in rename_map.items():
    df = df.withColumnRenamed(old, new)

# Keep the three partition columns and all other columns.
# Spark/Glue creates a partitioned Parquet dataset:
# output/city=<city>/state=<state>/country=<country>/...
output_path = args["OUTPUT_PATH"]

(
    df.write
    .mode("append")
    .format("parquet")
    .partitionBy("city", "state", "country")
    .save(output_path)
)

print(f"Wrote partitioned Parquet to: {output_path}")

job.commit()
