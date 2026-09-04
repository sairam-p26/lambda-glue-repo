# Lambda + Glue + S3 + CloudFormation + GitHub OIDC

This repository demonstrates a GitHub Actions CI/CD pipeline that authenticates to AWS using GitHub OIDC and deploys:

- Amazon S3 bucket
- AWS Lambda function
- AWS Glue ETL job
- IAM execution roles
- CloudFormation infrastructure

## Repository structure

```text
lambda-glue-repo/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── oidc-bootstrap/
│   └── trust-policy-example.json
├── sample/
│   └── input.csv
├── src/
│   ├── glue/
│   │   └── job.py
│   └── lambda/
│       └── handler.py
├── .gitignore
├── README.md
└── template.yaml
```

## Before pushing

1. Create the GitHub OIDC provider in AWS IAM if it does not already exist.
2. Create an IAM role trusted by GitHub OIDC.
3. Give that GitHub Actions role permission to deploy the CloudFormation stack and pass the application IAM roles.
4. Replace the placeholders in `oidc-bootstrap/trust-policy-example.json` with your GitHub username/repository.
5. Add the resulting IAM role ARN to GitHub repository **Settings → Secrets and variables → Actions** as `AWS_ROLE_ARN`.

## Deployment flow

The workflow first creates the S3 bucket. It then uploads the Lambda ZIP, Glue script, and sample CSV. Finally, it updates the CloudFormation stack to create the Lambda and Glue resources.

Push to `main` or `develop` to run the deployment.
