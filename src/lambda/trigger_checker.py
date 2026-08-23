import csv
import io
import logging
import os
from typing import Dict, List

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
glue = boto3.client("glue")

REQUIRED_COLUMNS = [col.strip() for col in os.environ.get("REQUIRED_COLUMNS", "id,name,city,state,country").split(",") if col.strip()]
GLUE_JOB_NAME = os.environ["GLUE_JOB_NAME"]
GLUE_SCRIPT_KEY = os.environ.get("GLUE_SCRIPT_KEY", "glue-scripts/partition_job.py")
OUTPUT_BASE_PREFIX = os.environ.get("OUTPUT_BASE_PREFIX", "output")


def lambda_handler(event: Dict, context) -> Dict:
    logger.info("Received event: %s", event)

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if not key.lower().endswith(".csv"):
            logger.info("Skipping non-CSV object: %s", key)
            continue

        if not key.startswith("input/"):
            logger.info("Skipping object outside input/ prefix: %s", key)
            continue

        if not has_required_columns(bucket, key):
            logger.warning("Required columns are missing. Skipping Glue job for %s/%s", bucket, key)
            continue

        deploy_glue_script(bucket)

        response = glue.start_job_run(
            JobName=GLUE_JOB_NAME,
            Arguments={
                "--INPUT_S3_PATH": f"s3://{bucket}/{key}",
                "--OUTPUT_BASE_PATH": f"s3://{bucket}/{OUTPUT_BASE_PREFIX}",
            },
        )

        job_run_id = response.get("JobRunId")
        logger.info("Started Glue job %s for object %s/%s", job_run_id, bucket, key)

    return {"status": "completed"}


def has_required_columns(bucket: str, key: str) -> bool:
    try:
        response = s3.get_object(Bucket=bucket, Key=key, Range="bytes=0-8191")
        raw = response["Body"].read().decode("utf-8", errors="replace")
        header_line = raw.splitlines()[0] if raw else ""
        reader = csv.reader(io.StringIO(header_line))
        headers = next(reader, [])
        logger.info("Parsed headers: %s", headers)

        missing = [column for column in REQUIRED_COLUMNS if column not in headers]
        if missing:
            logger.warning("Missing required columns: %s", missing)
            return False

        return True
    except ClientError as error:
        logger.error("Failed to read object %s/%s: %s", bucket, key, error)
        return False


def deploy_glue_script(bucket: str) -> None:
    try:
        s3.head_object(Bucket=bucket, Key=GLUE_SCRIPT_KEY)
        logger.info("Glue script already exists at s3://%s/%s", bucket, GLUE_SCRIPT_KEY)
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code")
        if error_code == "404":
            upload_glue_script(bucket)
        else:
            logger.exception("Unable to verify Glue script presence")
            raise


def upload_glue_script(bucket: str) -> None:
    script_path = os.path.join(os.path.dirname(__file__), "glue_scripts", "partition_job.py")
    logger.info("Uploading Glue script from %s", script_path)

    with open(script_path, "rb") as script_file:
        s3.put_object(Bucket=bucket, Key=GLUE_SCRIPT_KEY, Body=script_file, ContentType="text/x-python")
    logger.info("Uploaded Glue script to s3://%s/%s", bucket, GLUE_SCRIPT_KEY)
