import json
import logging
import random
import requests
from bs4 import BeautifulSoup
from slack import WebClient
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# process the rebus SQS
# 1. Select a rebus
# 2. Get the answer
# 3. Post the answer in a DM to the requestor
# 4. Post the rebus pic URL and tell slack to unfurl it

def lambda_handler(event, context):
    record = event['Records'][0]

    msg_map = record['body'].replace("'", '"')
    msg_map = json.loads(msg_map)

    level = "easy"
    if "text" in msg_map:
        test_level = msg_map['text'].lower()
        if test_level in ['easy', 'medium', 'hard']:
            level = test_level

    logger.info("level: {}".format(level))

    (rebus_url, rebus_image_url, clue, answer) = get_rebus(level)

    logger.info("rebus url: {}".format(rebus_url))
    logger.info("image url: {}".format(rebus_image_url))
    logger.info("clue: {}".format(clue))
    logger.info("answer: {}".format(answer))

    send_answer("@{}".format(msg_map['user_name']),
                "Level: {}\nRebus page: {}\nClue: {}\nAnswer: {}".format(level, rebus_url, clue, answer))

    # use the response_url to send the rebus
    response = {
        'response_type': 'in_channel',
        'text': "level: {}\n{}".format(level, rebus_image_url),
        'attachments': [
            {
                'image_url': rebus_image_url
            }
        ],
        'unfurl_media': True,
        'unfurl_links': True
    }

    logger.info("sending to slack: \n{}".format(response))

    url = msg_map['response_url']

    r = requests.post(url, json=response)

    # and gracefully close this function down . .

    return {}


def send_answer(user, message):
    SLACK_TOKEN = os.environ['SLACK_TOKEN']  # prob starts with xoxb-
    # Get one from https://api.slack.com/docs/oauth-test-tokens

    sc = WebClient(SLACK_TOKEN)

    sc.chat_postMessage(
        channel=user,
        text=message
    )


def get_rebus(level="easy"):
    image_url = ""
    rebus_url = ""
    clue = ""
    answer = ""
    found = False

    # not a whole lot of error checking going on here . . .
    # Select a random free rebus from rebuses.co by doing some page scraping.
    # If/when the page format changes, this will break :(
    while not found:
        page_number = random.randint(1, 99)
        page = requests.get('https://www.rebuses.co/free/page/{}/'.format(page_number))

        if page.status_code == 200:
            soup = BeautifulSoup(page.text, 'html.parser')
            articles = soup.body.findAll('article', {'class': 'article-archive'})

            level_rebuses = []
            # get all of the "level" rebuses on the page and randomly select on if > 1
            for article in articles:

                text = article.get_text().lower()
                if text.find(level) != -1:
                    level_rebuses.append(article)

            rebus_count = len(level_rebuses)

            if rebus_count > 1:
                index = random.randint(0, rebus_count - 1)

                rebus = level_rebuses[index]

                rebus_url = rebus.find('a').get('href')
                img = rebus.find('img')
                image_url = img['src']

                (clue, answer) = get_answer(rebus)
                found = True

    return (rebus_url, image_url, clue, answer)


def get_answer(article):
    # get the answer by doing some more scraping.  If/when the page format
    # changes this will break :(

    h2 = article.find('h2')
    url = h2.find('a').get('href')
    page = requests.get(url)

    if page.status_code == 200:
        soup = BeautifulSoup(page.text, 'html.parser')

        divs = soup.body.findAll('div', {'class': 'toggle-inner'})
        clue = divs[0].get_text()
        answer = divs[1].get_text()

        return (clue, answer)

    return ("", "")