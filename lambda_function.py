import json
import logging
from urllib import parse as urlparse
import base64
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    # Slack expects a response within 3s of making the request.  We cannot
    # usually get a full formed response with a rebus in that amount of time.
    # So, check that the request makes sense.  If it doesn't, respond with
    # the error.  If the request does make sense, send the request as a msg
    # to an SQS, respond to the slack user and let them know the request is
    # being processed and let the other lambda function complete the request.

    msg_map = dict(urlparse.parse_qsl(
        base64.b64decode(str(event['body'])).decode('ascii')))  # data comes b64 and also urlencoded name=value& pairs

    level = "easy"
    if "text" in msg_map:
        level = msg_map['text'].lower()

    ack = {}

    if level in ['easy', 'medium', 'hard']:
        article = "a"
        if level == "easy":
            article = "an"

        # put the msg_map into the SQS queue so it gets processed
        msg = send_sqs_message('rebus', msg_map)
        if msg is not None:
            logging.info("Sent SQS message ID: {}".format(msg["MessageId"]))
            ack = {
                "text": "Finding {} {} rebus for you.  One sec please . . .".format(article, level),
                "response_type": "in_channel"
            }
        else:
            logging.info("Did not queue up message")
            ack = {
                "text": "Hmmmm, something went wrong.  Please try again.",
                "response_type": "in_channel"
            }

    elif level in ['info', 'help']:
        ack = {
            "text": "I can find a rebus for you to solve!\nI can find an easy, medium or hard difficulty puzzle and will put the answer in a DM.\nTry '/rebus easy' to get started.",
            "response_type": "in_channel"
        }

    else:
        ack = {
            "text": "Sorry, I don't understand what you want.  Try '/rebus info' or '/rebus easy' to get started."
        }

    return ack


def send_sqs_message(QueueName, msg_body):
    """

    :param sqs_queue_url: String URL of existing SQS queue
    :param msg_body: String message body
    :return: Dictionary containing information about the sent message. If
        error, returns None.
    """

    # Send the SQS message
    sqs_client = boto3.client('sqs')
    sqs_queue_url = sqs_client.get_queue_url(QueueName=QueueName)['QueueUrl']
    try:
        msg = sqs_client.send_message(QueueUrl=sqs_queue_url,
                                      MessageBody=json.dumps(msg_body))
    except ClientError as e:
        logging.error(e)
        return None
    return msg