import csv
import io
import json
import os
import urllib.parse

import boto3


s3 = boto3.client("s3")
glue = boto3.client("glue")


REQUIRED_COLUMNS = {
    "city",
    "state",
    "country"
}


def lambda_handler(event, context):

    print("==========================================")
    print("LAMBDA VALIDATION STARTED")
    print("==========================================")

    print("Received EventBridge event:")
    print(json.dumps(event))


    detail = event.get("detail", {})


    bucket = (
        detail
        .get("bucket", {})
        .get("name")
    )


    key = urllib.parse.unquote_plus(
        detail
        .get("object", {})
        .get("key", "")
    )


    if not bucket or not key:
        raise ValueError(
            "Missing bucket or object key in EventBridge event"
        )


    print(f"Bucket: {bucket}")
    print(f"Key: {key}")


    # Only process files inside input/
    if not key.startswith("input/"):

        print("File is outside input/ prefix. Ignoring.")

        return {
            "status": "ignored",
            "reason": "File is outside input prefix"
        }


    # Only process CSV files
    if not key.lower().endswith(".csv"):

        print("File is not a CSV. Ignoring.")

        return {
            "status": "ignored",
            "reason": "File is not CSV"
        }


    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )


    body = response["Body"].read(
        1024 * 1024
    ).decode(
        "utf-8-sig"
    )


    lines = body.splitlines()


    if not lines:

        print("CSV file is empty.")

        return {
            "status": "validation_failed",
            "reason": "CSV file is empty"
        }


    # Read CSV header
    reader = csv.reader(
        io.StringIO(lines[0])
    )


    columns = {
        column.strip().lower()
        for column in next(reader, [])
    }


    print(f"Columns found: {sorted(columns)}")


    missing_columns = sorted(
        REQUIRED_COLUMNS - columns
    )


    if missing_columns:

        print(
            f"Validation failed. Missing columns: "
            f"{missing_columns}"
        )

        return {
            "status": "validation_failed",
            "bucket": bucket,
            "key": key,
            "missing_columns": missing_columns
        }


    print("CSV validation successful.")


    glue_job_name = os.environ[
        "GLUE_JOB_NAME"
    ]


    target_path = (
        f"s3://{bucket}/output/"
    )


    print(
        f"Starting Glue job: {glue_job_name}"
    )


    glue_run = glue.start_job_run(
        JobName=glue_job_name,
        Arguments={
            "--SOURCE_PATH": f"s3://{bucket}/{key}",
            "--TARGET_PATH": target_path
        }
    )


    job_run_id = glue_run["JobRunId"]


    print(
        f"Glue job started successfully: {job_run_id}"
    )


    return {
        "status": "glue_started",
        "job_name": glue_job_name,
        "job_run_id": job_run_id,
        "source": f"s3://{bucket}/{key}",
        "target": target_path
    }