"""
Message queue client using the STOMP 1.0 protocol
It requires the following environment variables defined

MQ_URI: Uri to connect to the message broker. For example: tcp://openmqhost:7672
MQ_DEST: Destination queue, it must start with /queue. For example /queue/PubScore.Q
MQ_USER and MQ_PASSWORD: The credentials to publish on the message queue
"""
from datetime import date
from os import getenv

from stompest.sync.client import Stomp
from stompest.config import StompConfig
from stompest.protocol import StompSpec

_MQ_URI = getenv("MQ_URI")
_MQ_DEST = getenv("MQ_DEST")
_MQ_USER = getenv("MQ_USER")
_MQ_PASS = getenv("MQ_PASSWORD")


class MessageClient:
    """
    STOMP sync client
    """

    def __init__(self, stomp_config: StompConfig):
        self.client = Stomp(stomp_config)

    def publish_model_score(self, score_date: date, score_value: float):
        """
        Publishes the score date and value on the message queue
        """
        self.client.connect(headers={'passcode': _MQ_PASS, 'login': _MQ_USER})
        message = 'date={0}\nvalue={1}'.format(score_date, str(score_value))
        self.client.send(_MQ_DEST, body=message)
        self.client.disconnect()

    def close(self):
        """
        Closes the session and transport, flushing the active subscription
        """
        self.client.close(flush=True)


def build_message_client() -> MessageClient:
    """
    Builds an instance of MessageClient provided all environment variables are defined
    """
    if not _MQ_URI:
        raise KeyError('MQ_URI environment variable missing')
    if not _MQ_DEST:
        raise KeyError('MQ_DEST environment variable missing')
    if not _MQ_USER or not _MQ_PASS:
        raise RuntimeError('MQ user credentials are missing')
    stomp_config = StompConfig(_MQ_URI, version=StompSpec.VERSION_1_0)
    return MessageClient(stomp_config)
