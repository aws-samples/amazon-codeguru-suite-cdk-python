#!/bin/bash

for i in {1..5}
do
aws sqs send-message --queue-url "$SQS_QUEUE_URL" --message-body "{\"test\": \"GA-latest\"}"
echo "Message $i sent to SQS queue"
sleep 20
done