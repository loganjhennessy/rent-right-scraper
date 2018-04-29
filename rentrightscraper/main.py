import json

from concurrent import futures

from google.cloud import pubsub_v1

from rentrightscraper.contentscraper import ContentScraper
from rentrightscraper.util.log import get_configured_logger

logger = get_configured_logger("rentrightscraper.main")


def callback(message):
    logger.info("Received message: {}".format(message))
    msg = json.loads(message.data.decode("utf-8"))
    contentscraper = ContentScraper()
    contentscraper.execute(msg)
    logger.info("No errors encountered processing message, acknowleding.")
    message.ack()


def main():
    project = "rent-right-dev"
    subscription_name = "listings"

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project, subscription_name)
    flow_control = pubsub_v1.types.FlowControl(max_messages=5)
    executor = futures.ThreadPoolExecutor(max_workers=2)
    subscriber = pubsub_v1.subscriber.policy.thread.Policy(
        subscriber, subscription_path, executor=executor, flow_control=flow_control
    )

    future = subscriber.open(callback)

    try:
        future.result()
    except Exception as e:
        print(
            "Listening for messages on {} threw an Exception: {}".format(
                subscription_name, e
            )
        )


if __name__ == "__main__":
    main()