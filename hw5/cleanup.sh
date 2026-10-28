#!/bin/bash

PROJECT_ID="adefifp22909"
REGION="us-central1"
ZONE="us-central1-a"
INSTANCE_NAME="hw5-db-instance"
STATIC_IP_NAME="hw5-webserver-static-ip"
VM_NAME="vm-webserver"

gcloud sql instances patch "$INSTANCE_NAME" \
    --activation-policy=NEVER \
    --project="$PROJECT_ID" \
    --quiet || true

gcloud compute instances delete "$VM_NAME" \
    --zone="$ZONE" \
    --project="$PROJECT_ID" \
    --quiet || true

gcloud compute instances delete vm-client \
    --zone="$ZONE" \
    --project="$PROJECT_ID" \
    --quiet || true

gcloud compute addresses delete "$STATIC_IP_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --quiet || true

gcloud auth application-default revoke --quiet || true
