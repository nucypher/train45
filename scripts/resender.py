#!/usr/bin/python3

import click
import requests
from ape import project
from ape.api import AccountAPI
from ape.cli import ConnectedProviderCommand, account_option
from ape.contracts import ContractInstance
from ape.logging import logger


def get_release_events(graphql_endpoint: str) -> list[dict]:
    """
    Queries GraphQL endpoint to retrieve all new `Release` events
    on Polygon network
    """

    gql = (
        """
    query ReleasetoResend {
    releaseds(
        where: {releaseTxSender: "0x0000000000000000000000000000000000000000", releaseResent: false}
        ) {
            id
        }
    }
    """
    )

    s = requests.session()
    s.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    response = s.post(graphql_endpoint, json={"query": gql})
    if response.status_code != 200:
        raise Exception(f"GraphQL endpoint not reachable [Error {response.status_code} - {response.text}]")

    data = response.json()
    messages = data["data"]["releaseds"]
    return messages


def resend_tx(
    account: AccountAPI, taco_child_app: ContractInstance, staker: str
) -> bool:
    """Sends `resendRelease` tx"""

    taco_child_app.resendRelease(staker, sender=account)


def resend(
    account: AccountAPI,
    taco_child_app: ContractInstance,
    messages: list[dict]
) -> int:
    """
    Iterates over all new messages, checks proof for each of them
    and executes tx on Ethereum side of the channel
    """

    processed = 0
    for event in messages:
        staker = event["id"]
        resend_tx(account, taco_child_app, staker)
        processed += 1

    return processed


@click.command(cls=ConnectedProviderCommand)
@account_option()
@click.option(
    "--taco-child-application",
    "-tca",
    help="Address of TACoChildApplication contract",
    default=None,
    required=True,
    type=click.STRING,
)
@click.option(
    "--graphql-endpoint",
    "-ge",
    help="GraphQL endpoint",
    default=None,
    required=True,
    type=click.STRING,
)
def cli(account, taco_child_application, graphql_endpoint):
    """Resends `release` tx on child network"""

    account.set_autosign(enabled=True)
    application = project.ITACoChildApplication.at(taco_child_application)

    messages = get_release_events(graphql_endpoint)
    logger.info("Got %d messages", len(messages))

    if len(messages) == 0:
        logger.info("No new transactions")
        return

    processed = resend(
        account, application, messages
    )
    logger.info("Processed %d transactions", processed)
