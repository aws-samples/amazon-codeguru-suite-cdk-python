# Github Actions CICD Pipeline integrated with CodeGuru Reviewer, Security, and Profiler.

This repository contains a GitHub Actions workflow that implements a Continuous Integration and Continuous Deployment (CI/CD) pipeline that reviews, analyses, and provides recommendations for your code using CodeGuru Reviewer, Profiler, and Security before it deploys your application code and infrastructure on AWS using CDK. The pipeline is triggered on pull requests to the `main` branch and performs the following tasks:

![Alt text](diagrams/ArchDiagram.jpg?raw=true)

## Pipeline Steps

1. **Checkout Code**: Checks out the repository code.

2. **Configure AWS Credentials**: Configures AWS credentials by assuming a specified IAM role `ROLE_TO_ASSUME` which will be used as the GitHub Actions role.

3. **CodeGuru Reviewer**: Runs the AWS CodeGuru Reviewer to analyze the code for potential issues and best practices. A link to the CodeGuru Review Dashboard in the AWS Console will be provided to show recommendations for the code.

4. **CodeGuru Security**: Runs the AWS CodeGuru Security to scan the code for potential security vulnerabilities and prints the findings. If the scan encounters a "Critical" finding, then the deployment fails; otherwise, the deployment continues. This step also prints out the dashboard link for the AWS CodeGuru Security console related to the security findings on the pull request for a better view of the findings, metrics, and recommendations.

5. **Approval Step**: Creates an issue in the repo for the approvers to review the findings. This will notify both the approvers and the developer who opened the pull request. The pipeline will fail on deny and will continue the app deployment on approval. Both parties will be notified of the outcome.

> If and once all approvers respond with an approved keyword, the workflow will continue.
If any of the approvers responds with a denied keyword, then the workflow will exit with a failed status.
Approval keywords - "approve", "approved", "lgtm", "yes"
Denied keywords - "deny", "denied", "no". For Usage and customizing approved/denied keywords check action `trstringer/manual-approval@v1` usage [here](https://github.com/marketplace/actions/manual-workflow-approval#usage)
   
7. **Synth**: Synthesizes the CDK app into an AWS CloudFormation template. The app is a simple lambda function that performs compute intensive tasks which will be analyzed using CodeGuru profiler.

8. **Deploy**: Deploys the CDK app to the AWS account. The stack includes the application python code to be deployed in Lambda and as well the CodeGuru profiler resources for profiling.

9. **Invoke Function using SQS**: Sends five test messages to the SQS queue that invokes the Lambda function hosting the application multiple times to generate enough data for CodeGuru profiling.

## Usage

This pipeline is automatically triggered on pull requests to the `main` branch. You can view the pipeline runs and logs in the "Actions" tab of the repository.

## Configuration

The pipeline uses several secrets and variables that need to be configured in the repository settings:

- `AWS_ACCOUNT_ID`: The AWS account ID where the pipeline will be executed.
- `ROLE_TO_ASSUME`: The name of the IAM role that the pipeline will assume. Use the role name `githubActionsDeployRole` that is created in the prerequisites stage.
- `CodeGuruReviewArtifactBucketName`: The name of the S3 bucket where CodeGuru Reviewer artifacts will be stored. Use the bucket name `codeguru-reviewer-build-artifacts-<ACCOUNT_ID>-<REGION>` that is created in the prerequisites stage.
> If using a custom role name for `ROLE_TO_ASSUME` and bucket name for `CodeGuruReviewArtifactBucketName`, you need to make sure to set up the necessary permissions required to run the CI pipeline.

**Repository Variables**
- `AWS_REGION`: The AWS region where the resources are located.

## CodeGuru Security Findings and Recommendation Output


## Contributing

If you want to contribute to this repository, please follow the standard GitHub workflow:

1. Fork the repository
2. Create a new branch for your changes
3. Make your changes and commit them
4. Push your changes to your forked repository
5. Create a pull request to the `main` branch of this repository

The CI/CD pipeline will automatically run on your pull request, and the changes will be reviewed before merging.

