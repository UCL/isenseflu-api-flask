"""
 Tests STOMP messaging client
"""

from datetime import date
from unittest import TestCase
from unittest.mock import patch, Mock

from scheduler.message_client import build_message_client, MessageClient


class MessageClientTestCase(TestCase):
    """ Test case for scheduler.message_client.py """

    def test_build_client(self):
        """
        Evaluate creation of an instance of MessageClient
        """
        with patch.multiple('scheduler.message_client',
                            _MQ_URI='tcp://openmqhost:7672',
                            _MQ_DEST='/queue/PubTest.Q',
                            _MQ_USER='testuser', _MQ_PASS='testpass'):
            instance = build_message_client()
            self.assertIsInstance(instance, MessageClient)

    def test_publish_model_score(self):
        """
        Publish a model score and date in the message queue
        """
        with patch.multiple('scheduler.message_client',
                            _MQ_URI='tcp://mock:7672',
                            _MQ_DEST='/queue/PubTest.Q',
                            _MQ_USER='testuser', _MQ_PASS='testpass'):
            instance = build_message_client()
            instance.client = Mock()
            instance.client.send = Mock()
            instance.publish_model_score(date(2018, 1, 1), 1.0)
            self.assertEqual(instance.client.send.call_count, 1)
            self.assertEqual(instance.client.send.call_args[0], ('/queue/PubTest.Q',))
            self.assertEqual(instance.client.send.call_args[1]['body'], b'date=2018-01-01\nvalue=1.0')
