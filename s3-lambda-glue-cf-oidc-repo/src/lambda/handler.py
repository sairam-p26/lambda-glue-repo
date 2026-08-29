import csv
import io
import json
import os
import urllib.parse

import boto3

s3 = boto3.client("s3")
glue = boto3.client("glue")

REQUIRED_COLUMNS = {"city", "state", "country"}


def lambda_handler(event, context):
    print(json.dumps(event))

    detail = event.get("detail", {})
    bucket = detail.get("bucket", {}).get("name")
    key = urllib.parse.unquote_plus(
        detail.get("object", {}).get("key", "")
    )

    if not bucket or not key:
        raise ValueError("Missing bucket/key in EventBridge event")

    if not key.startswith("input/"):
        return {"status": "ignored", "reason": "Not an input object"}

    if not key.lower().endswith(".csv"):
        return {"status": "ignored", "reason": "Not a CSV file"}

    response = s3.get_object(Bucket=bucket, Key=key)

    # Read only enough data to inspect the header.
    body = response["Body"].read(1024 * 1024).decode("utf-8-sig")
    lines = body.splitlines()

    if not lines:
        return {"status": "validation_failed", "reason": "Empty CSV"}

    reader = csv.reader(io.StringIO(lines[0]))
    columns = {c.strip().lower() for c in next(reader, [])}

    missing = sorted(REQUIRED_COLUMNS - columns)

    if missing:
        print(f"Validation failed. Missing columns: {missing}")
        return {
            "status": "validation_failed",
            "bucket": bucket,
            "key": key,
            "missing_columns": missing,
        }

    job_name = os.environ["GLUE_JOB_NAME"]

    run = glue.start_job_run(
        JobName=job_name,
        Arguments={
            "--SOURCE_BUCKET": bucket,
            "--SOURCE_KEY": key,
            "--OUTPUT_PATH": f"s3://{bucket}/output/",
        },
    )

    print(f"Started Glue job: {run['JobRunId']}")

    return {
        "status": "glue_started",
        "job_name": job_name,
        "job_run_id": run["JobRunId"],
        "source": f"s3://{bucket}/{key}",
    }
