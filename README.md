# State Transfer Bot Polygon → Ethereum

Stateless bot monitors GraphQL endpoint for new events `MessageSent` that occurs on Polygon network. And then transfers proof to Ethereum root contract.

## Installation

We use [Ape](https://docs.apeworx.io/ape/stable/index.html) as the testing and deployment framework of this project.

### Configuring Pre-commit

To install pre-commit locally:

```bash
pre-commit install
```

## Example of usage

```bash
export WEB3_INFURA_PROJECT_ID=<Infura project ID>
export APE_ACCOUNTS_BOT_PASSPHRASE=<Passphrase for account with alias BOT>
export ETHERSCAN_API_KEY=<API Key for Etherscan>

ape run proof_bot --fx-root-tunnel 0x51825d6e893c51836dC9C0EdF3867c57CD0cACB3--graphql-endpoint https://subgraph.satsuma-prod.com/735cd3ac7b23/nucypher-ops/PolygonChild/api --proof-generator https://proof-generator.polygon.technology/api/v1/matic/exit-payload/ --block-check-api https://proof-generator.polygon.technology/api/v1/matic/block-included/ --network ethereum:mainnet:infura --account BOT
```


## Docker

##### Build

```bash
docker build -f deploy/Dockerfile -t nucypher/train45:latest .
```

##### Run

First, create the log file:

```bash
touch /var/log/cron.log
```

Then run the bot:

```bash
docker run             \
--name train45         \
--detach               \
--env-file .env        \
-f deploy/Dockerfile   \
-v /var/log/cron.log:/var/log/cron.log \
-v /var/log/:/var/log/ \
-v ~/.ape/:/root/.ape  \
nucypher/train45:latest
```

Enjoy the logs:

```bash
tail -f /var/log/cron.log
```

##### Stop

```bash
docker stop train45 && docker rm train45
```

## Docker-compose

##### Build

```bash
docker-compose build
```

##### Start (all services)

First, create the log file:

```bash
touch /var/log/cron.log
```

Then run the bot with docker-compose
(including log server and autoupdate service):

```bash
docker-compose up -d
```

##### Stop (all services)

```bash
docker-compose down
```
