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
    Queries GraphQL endpoint to retrieve stakers with a `CHILD_RELEASED`
    event that has no subsequent `CHILD_RELEASE_RESENT`.
    """

    gql = """
    query ReleasetoResend {
        released: authorizationEvents(
            where: {eventType: CHILD_RELEASED}
            first: 1000
        ) {
            stakingProvider { id }
            blockNumber
        }
        resent: authorizationEvents(
            where: {eventType: CHILD_RELEASE_RESENT}
            first: 1000
        ) {
            stakingProvider { id }
            blockNumber
        }
    }
    """

    s = requests.session()
    s.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    response = s.post(graphql_endpoint, json={"query": gql})
    if response.status_code != 200:
        raise Exception(f"GraphQL endpoint not reachable [Error {response.status_code} - {response.text}]")

    data = response.json()["data"]

    latest_resent: dict[str, int] = {}
    for event in data["resent"]:
        staker = event["stakingProvider"]["id"]
        block = int(event["blockNumber"])
        if block > latest_resent.get(staker, -1):
            latest_resent[staker] = block

    latest_released: dict[str, int] = {}
    for event in data["released"]:
        staker = event["stakingProvider"]["id"]
        block = int(event["blockNumber"])
        if block > latest_released.get(staker, -1):
            latest_released[staker] = block

    pending = [
        {"id": staker}
        for staker, released_block in latest_released.items()
        if released_block > latest_resent.get(staker, -1)
    ]
    return pending


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
