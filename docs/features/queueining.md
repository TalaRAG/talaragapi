# Queueing

## Settings

* `SQS_QUEUE`: Queue name or URL used for document-processing messages
* `AWS_ACCESS_KEY_ID`: AWS access key used when connecting to SQS
* `AWS_SECRET_ACCESS_KEY`: AWS secret key used when connecting to SQS
* `AWS_REGION`: AWS region used when connecting to SQS

## Payload Structure

A message in the queue should be a json payload with the following structure:

```json
{
    "document_id": "somedocumentid",
    "key": "s3_key"
}
```

`key` should contain the stored S3 object key for the uploaded document.

## Process

1. On document create, initial status should be `pending`
2. Backend should post the payload to the queue with `document_id` and `key`
