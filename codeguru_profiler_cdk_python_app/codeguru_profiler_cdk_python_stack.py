# cdk-nag is used in this project
import os
import shutil
import sys
import venv
from aws_cdk import (
    Aspects,
    Stack,
    aws_lambda as _lambda,
    aws_codeguruprofiler as codeguru,
    aws_iam as iam,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_lambda_event_sources as lambda_events,
    Duration,
    CfnOutput
)
from constructs import Construct
from cdk_nag import AwsSolutionsChecks, NagSuppressions

class CodeguruProfilerCdkPythonAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Add AWS Solutions Checks
        Aspects.of(self).add(AwsSolutionsChecks())

        # Create S3 bucket for I/O operations
        bucket = s3.Bucket(self, "CgBucket", enforce_ssl=True)

        # Create SQS queue
        self.queue = sqs.Queue(
            self, "CgQueue",
            queue_name="cdk-python-queue",
            visibility_timeout=Duration.seconds(300)  # 5 minutes
        )

        # Create CodeGuru Profiler Group
        profiler_group = codeguru.CfnProfilingGroup(
            self, "PythonAppProfilingGroup",
            profiling_group_name="cdk-python-profiling-group",
            compute_platform="AWSLambda"
        )

        # Prepare Lambda code and dependencies
        lambda_code_path = os.path.join(os.path.dirname(__file__), '..', 'lambda')
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'lambda_output')
        
         # Clean up old output directory if it exists
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        
        os.makedirs(output_dir)
        
        # Create a virtual environment and install dependencies
        venv.create(output_dir, with_pip=True)

        # Activate the virtual environment
        venv_path = os.path.join(output_dir, 'lib', 'python3.9', 'site-packages')
        sys.path.insert(0, venv_path)

        # Install dependencies using pip
        requirements_path = os.path.join(lambda_code_path, "requirements.txt")
        with open(requirements_path, 'r', encoding='utf-8') as f:
            requirements = f.read().splitlines()

        import pip
        pip.main(['install', '-t', output_dir] + requirements)

        # Remove the virtual environment path from sys.path
        sys.path.pop(0)
        
        # Copy Lambda function code
        shutil.copy2(os.path.join(lambda_code_path, "index.py"), output_dir)

        # Create Lambda function
        self.lambda_function = _lambda.Function(
            self, "PythonAppFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset(output_dir),
            environment={
                "CODEGURU_PROFILER_GROUP_NAME": profiler_group.profiling_group_name,
                "AWS_CODEGURU_PROFILER_ENABLED": "TRUE",
                "BUCKET_NAME": bucket.bucket_name,
                "QUEUE_URL": self.queue.queue_url,
                "AWS_CODEGURU_PROFILER_TARGET_REGION": "us-east-1"
            },
            timeout=Duration.seconds(300),  # 5 minutes
            memory_size=1024  # 1 GB memory
        )

        # Add SQS as event source for Lambda
        self.lambda_function.add_event_source(lambda_events.SqsEventSource(self.queue))

        # Grant Lambda function permissions to publish to CodeGuru Profiler
        self.lambda_function.add_to_role_policy(iam.PolicyStatement(
            actions=["codeguru-profiler:ConfigureAgent",
                     "codeguru-profiler:PostAgentProfile",
                     "codeguru-profiler:GetProfilingGroup",
                     "codeguru-profiler:DescribeProfilingGroup",
                     "codeguru-profiler:ListProfilingGroups",
                     "codeguru-profiler:CreateProfilingGroup",
                     "codeguru-profiler:UpdateProfilingGroup"],
            resources=["arn:aws:codeguru-profiler:*:*:profilingGroup/*"]
        ))

        # Add Lambda Layer for CodeGuru Profiler Agent
        self.lambda_function.add_layers(_lambda.LayerVersion.from_layer_version_arn(
            self, "CodeGuruProfilerAgentLayer",
            layer_version_arn="arn:aws:lambda:us-east-1:157417159150:layer:AWSCodeGuruProfilerPythonAgentLambdaLayer:11"
        ))

        # Grant Lambda function permissions to read/write to S3 bucket
        bucket.grant_read_write(self.lambda_function)

        # Grant Lambda function permissions to read from SQS
        self.queue.grant_consume_messages(self.lambda_function)

        # Add suppressions for any rules you want to ignore
        NagSuppressions.add_stack_suppressions(self, [
            {"id": "AwsSolutions-S1", "reason": "S3 bucket is intentionally configured without server-side encryption for this demo."},
            {"id": "AwsSolutions-S10", "reason": "S3 bucket is intentionally configured without SSL for this demo."},
            {"id": "AwsSolutions-SQS4", "reason": "SQS queue is intentionally configured without server-side encryption for this demo."},
            {"id": "AwsSolutions-SQS3", "reason": "SQS queue is intentionally configured without server-side encryption for this demo."},
            {"id": "AwsSolutions-IAM4", "reason": "Wildcard permissions are used for demonstration purposes."},
            {"id": "AwsSolutions-IAM5", "reason": "Wildcard permissions are used for demonstration purposes."},
            {"id": "AwsSolutions-L1", "reason": "Lambda function is intentionally configured for this demo."}

        ])

        # Output the profiling group name, Lambda function name, and SQS queue URL
        CfnOutput(self, "ProfilingGroupName", value=profiler_group.profiling_group_name)
        CfnOutput(self, "LambdaFunctionName", value=self.lambda_function.function_name)
        CfnOutput(self, "S3BucketName", value=bucket.bucket_name)
        CfnOutput(self, "SQSQueueUrl", value=self.queue.queue_url)

        # Get the queue URL
        self.queue_url = self.queue.queue_url

    @property
    def get_lambda_function(self):
        return self.lambda_function
    
    @property
    def get_queue_url(self):
        return self.queue_url