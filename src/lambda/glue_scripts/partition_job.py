import sys

from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

args = getResolvedOptions(sys.argv, ["INPUT_S3_PATH", "OUTPUT_BASE_PATH"])
input_path = args["INPUT_S3_PATH"]
output_base = args["OUTPUT_BASE_PATH"]

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

required_columns = ["id", "name", "city", "state", "country"]

print(f"Reading CSV from {input_path}")
raw_df = spark.read.option("header", "true").option("inferSchema", "true").csv(input_path)
columns = [col.lower() for col in raw_df.columns]

missing = [col for col in required_columns if col not in columns]
if missing:
    raise ValueError(f"Glue job input is missing required columns: {missing}")

for field in ["city", "state", "country"]:
    output_path = f"{output_base}/by_{field}"
    print(f"Writing partitioned output to {output_path}")
    raw_df.write.mode("overwrite").partitionBy(field).option("header", "true").csv(output_path)

print("Glue job completed successfully")
