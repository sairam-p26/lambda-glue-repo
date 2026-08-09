# Lambda Glue Repo

This repository contains an AWS SAM deployment for a data pipeline that:

- creates an S3 bucket for input and output data
- deploys a Lambda function triggered by S3 object uploads
- validates CSV files for required columns
- starts an AWS Glue job when validation succeeds
- partitions output data by `city`, `state`, and `country`

## Repository structure

- `template.yaml` - AWS SAM template defining the S3 bucket, Lambda, IAM roles, and Glue job
- `src/lambda/trigger_checker.py` - Lambda function code
- `src/lambda/glue_scripts/partition_job.py` - Glue ETL script
- `.github/workflows/deploy.yml` - GitHub Actions workflow using OIDC to assume an AWS role

## How it works

1. Push to `main` or `develop` triggers GitHub Actions.
2. The workflow uses `aws-actions/configure-aws-credentials@v3` with OIDC and `AWS_ROLE_ARN` secret.
3. SAM builds and deploys the stack.
4. Files uploaded to `s3://<bucket>/input/` with `.csv` extension invoke the Lambda function.
5. Lambda validates required columns: `id`, `name`, `city`, `state`, `country`.
6. If valid, Lambda starts the Glue job.
7. Glue partitions the input data by `city`, `state`, and `country` into `s3://<bucket>/output/`.

## GitHub Actions setup

- Create a repository secret `AWS_ROLE_ARN` with the IAM role ARN that GitHub should assume.
- Ensure OIDC trust is configured in AWS for `token.actions.githubusercontent.com`.

## Deploying manually

```bash
aws cloudformation package \
  --template-file template.yaml \
  --s3-bucket <deployment-bucket> \
  --output-template-file packaged.yaml

aws cloudformation deploy \
  --template-file packaged.yaml \
  --stack-name lambda-glue-pipeline \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```
