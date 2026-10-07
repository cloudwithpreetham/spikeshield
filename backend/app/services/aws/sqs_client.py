import boto3
import json
import uuid
from botocore.exceptions import ClientError

class SQSClient:
    def __init__(self, settings):
        self.settings = settings
        if not settings.MOCK_AWS:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            self.client = boto3.client('sqs', **kwargs)

    def send_runbook_message(self, runbook_type: str, payload: dict) -> str:
        if self.settings.MOCK_AWS: return str(uuid.uuid4())
        try:
            response = self.client.send_message(QueueUrl=self.settings.SQS_RUNBOOK_QUEUE_URL, MessageBody=json.dumps({"type": runbook_type, "payload": payload}))
            return response.get('MessageId')
        except ClientError: return ""

    def receive_messages(self, max_messages: int = 10) -> list[dict]:
        if self.settings.MOCK_AWS: return []
        try:
            response = self.client.receive_message(QueueUrl=self.settings.SQS_RUNBOOK_QUEUE_URL, MaxNumberOfMessages=max_messages)
            return response.get('Messages', [])
        except ClientError: return []

    def delete_message(self, receipt_handle: str) -> None:
        if self.settings.MOCK_AWS: return
        try:
            self.client.delete_message(QueueUrl=self.settings.SQS_RUNBOOK_QUEUE_URL, ReceiptHandle=receipt_handle)
        except ClientError: pass
