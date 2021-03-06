from __future__ import absolute_import, unicode_literals

import boto3
from botocore.exceptions import ClientError

from eb_sqs import settings
from eb_sqs.worker.queue_client import QueueClient, QueueDoesNotExistException, QueueClientException


class SqsQueueClient(QueueClient):
    def __init__(self):
        # type: () -> None
        self.sqs = boto3.resource('sqs')
        self.queue_cache = {}

    def _get_queue(self, queue_name):
        # type: (unicode) -> Any
        queue_name = '{}{}'.format(settings.QUEUE_PREFIX, queue_name)

        queue = self._get_sqs_queue(queue_name)
        if not queue:
            queue = self._add_sqs_queue(queue_name)

        return queue

    def _get_sqs_queue(self, queue_name):
        # type: (unicode) -> Any
        if self.queue_cache.get(queue_name):
            return self.queue_cache[queue_name]

        try:
            queue = self.sqs.get_queue_by_name(QueueName=queue_name)
            self.queue_cache[queue_name] = queue
            return queue
        except ClientError as ex:
            error_code = ex.response.get('Error', {}).get('Code', None)
            if error_code == 'AWS.SimpleQueueService.NonExistentQueue':
                return None
            else:
                raise ex

    def _add_sqs_queue(self, queue_name):
        # type: (unicode) -> Any
        if settings.AUTO_ADD_QUEUE:
            queue = self.sqs.create_queue(QueueName=queue_name)
            self.queue_cache[queue_name] = queue
            return queue
        else:
            raise QueueDoesNotExistException(queue_name)

    def add_message(self, queue_name, msg, delay):
        # type: (unicode, unicode, int) -> None
        try:
            queue = self._get_queue(queue_name)
            queue.send_message(
                MessageBody=msg,
                DelaySeconds=delay
            )
        except Exception as ex:
            raise QueueClientException(ex)
