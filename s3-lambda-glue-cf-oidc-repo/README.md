# S3 → Lambda → Glue → Partitioned Parquet (CloudFormation + GitHub OIDC)

This repository deploys an AWS data pipeline with **CloudFormation** and **GitHub Actions using OIDC authentication**.

## Architecture

```text
GitHub
  |
  | push to main
  v
GitHub Actions
  |
  | OIDC -> AWS IAM Role
  v
CloudFormation
  |
  +--> S3 data bucket
  +--> Lambda validation function
  +--> Glue job + Glue IAM role
  +--> EventBridge rule
  |
  v
S3 input/
  |
  v
EventBridge
  |
  v
Lambda
  |
  | validate required columns
  | start Glue job when valid
  v
AWS Glue
  |
  | read CSV
  | write Parquet
  | partitionBy(city,state,country)
  v
S3 output/
```

## Important behavior

1. Upload a CSV into `input/` in the data bucket.
2. S3 sends an object-created event to EventBridge.
3. Lambda reads the CSV header and checks that these columns exist:
   - `city`
   - `state`
   - `country`
4. If all columns exist, Lambda starts the Glue job.
5. Glue reads the CSV and writes a **partitioned Parquet dataset** under:
   `output/`
6. The partition layout is:
   `city=<city>/state=<state>/country=<country>/`

> Partitioning does **not** guarantee exactly three physical files. It creates partition folders/files based on the data and Spark's output behavior. If your requirement is literally "exactly 3 files", that is a different output design.

## Prerequisites

- AWS account
- GitHub repository
- AWS CLI
- Python 3.x
- An AWS IAM deployment role trusted by GitHub's OIDC provider
- GitHub Actions secret:
  `AWS_ROLE_ARN`

## OIDC setup

For the first deployment, create an IAM OIDC provider for:

`https://token.actions.githubusercontent.com`

Then create an IAM role trusted by that provider. Restrict the trust policy to your exact GitHub repository, for example:

```json
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
  },
  "StringLike": {
    "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_OWNER/YOUR_REPO:ref:refs/heads/main"
  }
}
```

Attach only the permissions your deployment needs. For a learning/demo environment, broad CloudFormation/IAM/S3/Lambda/Glue/EventBridge permissions are simpler, but production should use least privilege.

Put the resulting role ARN in GitHub:

`Settings -> Secrets and variables -> Actions -> New repository secret`

Name:

`AWS_ROLE_ARN`

Value:

`arn:aws:iam::<ACCOUNT_ID>:role/<ROLE_NAME>`

## Deploy with GitHub Actions

Update these values in `.github/workflows/deploy.yml`:

- `AWS_REGION`
- `STACK_NAME`
- `DATA_BUCKET_NAME` (optional; leaving it empty lets CloudFormation create a generated bucket name)

Then:

```bash
git add .
git commit -m "Add S3 Lambda Glue pipeline"
git push origin main
```

GitHub Actions will:

1. Authenticate to AWS with OIDC.
2. Package/deploy the CloudFormation stack.
3. Upload the Glue script to the deployment bucket created by the stack.
4. Update the Glue job to use that script.

## Test

Use the bucket name printed in the CloudFormation outputs.

Upload:

```text
sample/input.csv
```

to:

```text
s3://YOUR_BUCKET/input/input.csv
```

Example valid CSV:

```csv
id,name,city,state,country
1,Alice,Hyderabad,Telangana,India
2,Bob,Chennai,Tamil Nadu,India
3,John,Dallas,Texas,USA
```

The Lambda logs are in CloudWatch.

The Glue output will look approximately like:

```text
s3://YOUR_BUCKET/output/
  city=Chennai/state=Tamil%20Nadu/country=India/...
  city=Hyderabad/state=Telangana/country=India/...
  city=Dallas/state=Texas/country=USA/...
```

## Invalid CSV test

This file should fail validation:

```csv
id,name,city,state
1,Alice,Hyderabad,Telangana
```

Because `country` is missing, Lambda will not start Glue.

## Repository structure

```text
.
├── .github/
│   └── workflows/
│       └── deploy.yml
├── src/
│   ├── lambda/
│   │   └── handler.py
│   └── glue/
│       └── job.py
├── sample/
│   └── input.csv
├── .gitignore
├── README.md
└── template.yaml
```
