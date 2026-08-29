# AWS S3 → Lambda → Glue Data Pipeline

This project deploys AWS infrastructure using CloudFormation through GitHub Actions with AWS OIDC authentication.

## Architecture

GitHub Actions → CloudFormation → S3 → Lambda → Glue → S3

## Components

- S3 input/output bucket
- Lambda for CSV column validation
- AWS Glue ETL job
- CloudFormation infrastructure
- GitHub Actions CI/CD
- AWS IAM OIDC authentication
