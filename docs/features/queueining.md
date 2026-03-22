# Queueing

## Settings

* `SQS_QUEUE`: Environment variable to line up messages

## Payload Structure

A message in the queue should be a json payload with the following structure:

```json
{
    "document_id": "12345"
}
```

## Process

1. On document create, initial status should be `pending`
2. Backend should post the payload to the queue
