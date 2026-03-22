import json
import logging
import os
from urllib.parse import urlparse
from uuid import uuid4

import boto3


logger = logging.getLogger("talaragapi")


def configured_sqs_queue():
    return os.getenv("SQS_QUEUE", "").strip()


def enqueue_document(settings, document_id, key):
    queue = configured_sqs_queue()
    if not queue:
        logger.warning("Skipping enqueue for document_id=%s because SQS_QUEUE is not configured", document_id)
        return False

    client = boto3.client(
        "sqs",
        region_name=getattr(settings, "AWS_REGION", "") or _infer_sqs_region(queue) or None,
        endpoint_url=_infer_sqs_endpoint_url(queue),
    )
    queue_url = _resolve_sqs_queue_url(client, queue)
    payload = json.dumps({"document_id": document_id, "key": key})
    message = {
        "QueueUrl": queue_url,
        "MessageBody": payload,
    }

    if queue_url.endswith(".fifo"):
        message["MessageGroupId"] = str(document_id)
        message["MessageDeduplicationId"] = uuid4().hex

    logger.info("Enqueuing document_id=%s key=%s queue=%s", document_id, key, queue_url)
    client.send_message(**message)
    logger.info("Enqueued document_id=%s key=%s", document_id, key)
    return True


def _infer_sqs_region(queue):
    parsed = urlparse(queue)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""

    parts = parsed.netloc.split(".")
    if len(parts) >= 4 and parts[0] == "sqs" and parts[-2:] == ["amazonaws", "com"]:
        return parts[1]
    return ""


def _infer_sqs_endpoint_url(queue):
    parsed = urlparse(queue)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.netloc.endswith("amazonaws.com"):
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _resolve_sqs_queue_url(client, queue):
    if queue.startswith("http://") or queue.startswith("https://"):
        return queue
    response = client.get_queue_url(QueueName=queue)
    return response["QueueUrl"]
