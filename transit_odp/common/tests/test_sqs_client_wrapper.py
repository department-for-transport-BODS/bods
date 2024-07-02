import unittest
from unittest import skip
from unittest.mock import MagicMock, patch
from transit_odp.common.utils.aws_common import SQSClientWrapper


@skip("This test will be enabled when DQS feature is enabled")
class TestSQSClientWrapper(unittest.TestCase):
    @patch("transit_odp.common.utils.aws_common.boto3.client")
    def test_send_message_to_queue(self, mock_boto3_client):
        sqs_wrapper = SQSClientWrapper()

        mock_list_queues_response = {
            "QueueUrls": [
                "http://sqs.us-east-2.localhost.localstack.cloud:4566/000000000000/incorrect_licence_number_queue",
                "http://sqs.us-east-2.localhost.localstack.cloud:4566/000000000000/stops_not_found_in_queue",
            ]
        }

        mock_send_message = MagicMock()

        # Configure the mock boto3 client
        mock_boto3_client.return_value.list_queues.return_value = (
            mock_list_queues_response
        )
        mock_boto3_client.return_value.send_message = mock_send_message

        queues_payload = {
            "incorrect_licence_number_queue": [
                {"file_id": 16758, "check_id": 1, "result_id": 729}
            ],
            "stops_not_found_in_queue": [
                {"file_id": 16760, "check_id": 1, "result_id": 742}
            ],
        }

        sqs_wrapper.send_message_to_queue(queues_payload)

        mock_boto3_client.return_value.list_queues.assert_called_once()

        mock_send_message.assert_any_call(
            QueueUrl="http://sqs.us-east-2.localhost.localstack.cloud:4566/000000000000/incorrect_licence_number_queue",
            MessageBody='{"file_id": 16758, "check_id": 1, "result_id": 729}',
        )
        mock_send_message.assert_any_call(
            QueueUrl="http://sqs.us-east-2.localhost.localstack.cloud:4566/000000000000/stops_not_found_in_queue",
            MessageBody='{"file_id": 16760, "check_id": 1, "result_id": 742}',
        )

    @patch("transit_odp.common.utils.aws_common.boto3.client")
    def test_send_message_to_queue_queue_not_found(self, mock_boto3_client):
        sqs_wrapper = SQSClientWrapper()

        mock_list_queues_response = {
            "QueueUrls": [
                "http://sqs.us-east-2.localhost.localstack.cloud:4566/000000000000/incorrect_licence_number_queue",
            ]
        }

        mock_boto3_client.return_value.list_queues.return_value = (
            mock_list_queues_response
        )

        queues_payload = {
            "non_existing_queue": [{"file_id": 16758, "check_id": 1, "result_id": 729}]
        }

        sqs_wrapper.send_message_to_queue(queues_payload)

        mock_boto3_client.return_value.list_queues.assert_called_once()

        mock_boto3_client.return_value.send_message.assert_not_called()
