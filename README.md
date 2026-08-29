# AWS S3 → Lambda → Glue Data Pipeline

This project demonstrates an AWS data pipeline using Amazon S3, AWS Lambda, AWS Glue, CloudFormation, and GitHub Actions with AWS OIDC authentication.

## Architecture

```text
GitHub Actions
      ↓
CloudFormation
      ↓
     S3
      ↓
   Lambda
      ↓
    Glue
      ↓
     S3
```

## Components

* **Amazon S3** – Stores input and output data
* **AWS Lambda** – Validates CSV columns and processes the input file
* **AWS Glue** – Performs ETL processing on the data
* **AWS CloudFormation** – Creates and manages AWS infrastructure
* **GitHub Actions** – Automates deployment and CI/CD
* **AWS IAM OIDC** – Provides secure authentication between GitHub Actions and AWS

## Project Structure

```text
aws-s3-lambda-glue-pipeline/
│
├── s3-lambda-glue-cf-oidc-repo/
│   │
│   ├── oidc-bootstrap/
│   │   └── trust-policy-example.json
│   │
│   ├── sample/
│   │   └── input.csv
│   │
│   ├── src/
│   │   ├── lambda/
│   │   │   └── handler.py
│   │   │
│   │   └── glue/
│   │       └── job.py
│   │
│   ├── template.yaml
│   └── README.md
│
└── README.md
```

## Data Flow

1. A CSV file is uploaded to the S3 input bucket.
2. S3 triggers the Lambda function.
3. Lambda validates the CSV file and its columns.
4. AWS Glue reads the input data from S3.
5. Glue performs the required ETL transformations.
6. The processed data is written back to S3.
7. CloudFormation manages the AWS infrastructure.
8. GitHub Actions automates the deployment process using AWS OIDC authentication.

## Technologies Used

* Python
* Amazon S3
* AWS Lambda
* AWS Glue
* AWS CloudFormation
* AWS IAM
* GitHub Actions
* GitHub OIDC
* CSV / Parquet

## Deployment

The AWS infrastructure can be deployed using CloudFormation through GitHub Actions.

GitHub Actions authenticates with AWS using IAM OIDC instead of storing long-lived AWS access keys in GitHub.

## Purpose

The purpose of this project is to demonstrate a practical AWS Data Engineering pipeline and CI/CD deployment workflow.

---

**AWS S3 → Lambda → Glue → S3**
