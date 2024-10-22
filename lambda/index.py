import json
import boto3
import os
from codeguru_profiler_agent import with_lambda_profiler
from aws_lambda_powertools import Logger

# Set up logging
logger = Logger(service="CodeGuruProfilerCdkPythonApp")

s3 = boto3.client('s3')
sqs = boto3.client('sqs')

# Initialize the Profiler
profiler_group_name = os.environ.get('CODEGURU_PROFILER_GROUP_NAME')
logger.info(f"Initializing CodeGuru Profiler with group name: {profiler_group_name}")

def cpu_intensive_task():
    """Perform a CPU-intensive calculation."""
    logger.info("Starting CPU-intensive task")
    result = 0
    for i in range(1000000):
        result += i * i
    logger.info("Completed CPU-intensive task")
    return result

def io_intensive_task(bucket_name):
    """Perform I/O-intensive operations with S3."""
    logger.info(f"Starting I/O-intensive task with bucket: {bucket_name}")
    try:
        # Write to S3
        s3.put_object(Bucket=bucket_name, Key='test.txt', Body='Hello, World!')
        
        # Read from S3
        response = s3.get_object(Bucket=bucket_name, Key='test.txt')
        content = response['Body'].read()
        
        logger.info("Completed I/O-intensive task")
        return content
    except Exception as e:
        logger.warning(f"Error in I/O-intensive task: {str(e)}", exc_info=True)
        raise

def process_message(message_body):
    """Process the SQS message."""
    logger.info(f"Processing message: {message_body}")
    return f"Processed: {message_body}"

@with_lambda_profiler(profiling_group_name=profiler_group_name, region_name="us-east-1")
def handler(event, context):
    logger.info(f"Starting new invocation", extra={"lambda_function_arn": context.invoked_function_arn, "aws_request_id": context.aws_request_id, "aws_region": context.invoked_function_arn.split(":")[3]})
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        logger.info("Starting CodeGuru Profiler")

        # Perform CPU-intensive task
        cpu_result = cpu_intensive_task()
        
        # Perform I/O-intensive task
        bucket_name = os.environ.get('BUCKET_NAME')
        io_result = io_intensive_task(bucket_name)
        
        # Process SQS messages if present
        sqs_results = []
        if 'Records' in event:
            for record in event['Records']:
                message_body = record['body']
                result = process_message(message_body)
                sqs_results.append(result)
        else:
            # If no SQS messages, process a dummy message
            dummy_message = "Test message (no SQS event)"
            result = process_message(dummy_message)
            sqs_results.append(result)
        
        result = {
            "cpu_result": cpu_result,
            "io_result": io_result.decode('utf-8'),
            "sqs_results": sqs_results
        }
        
        logger.info(f"Function completed successfully. Result: {json.dumps(result)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except Exception as e:
        logger.warning(f"Error in Lambda function: {str(e)}", exc_info=True)
        raise