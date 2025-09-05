#!/bin/bash

cd /app
echo "The train is leaving the station"
ape run proof_bot \
--network $ETH_NETWORK      \
--account $ACCOUNT          \
--fx-root-tunnel $TUNNEL    \
--graphql-endpoint $GQL_URL \
--proof-generator $PROOFS_URL

ape run resender \
--network $POLYGON_NETWORK \
--taco-child-application $TACO_CHILD_APPLICATION_ADDRESS \
--account $ACCOUNT \
--graphql-endpoint $GQL_URL
