#!/bin/bash
set -e

PROJECT_ID="adefifp22909"
REGION="us-central1"
ZONE="us-central1-a"
INSTANCE_NAME="hw5-db-instance"
DB_NAME="cs528_hw5"
DB_ROOT_PASSWORD="cs528password"
STATIC_IP_NAME="hw5-webserver-static-ip"
VM_NAME="vm-webserver"

handle_cloud_sql() {
    if gcloud sql instances describe "$INSTANCE_NAME" --project="$PROJECT_ID" > /dev/null 2>&1; then
        gcloud sql instances patch "$INSTANCE_NAME" \
            --activation-policy=ALWAYS \
            --project="$PROJECT_ID" \
            --quiet
    else
        gcloud sql instances create "$INSTANCE_NAME" \
            --database-version=MYSQL_8_0 \
            --tier=db-custom-1-3840 \
            --region="$REGION" \
            --root-password="$DB_ROOT_PASSWORD" \
            --authorized-networks=0.0.0.0/0 \
            --project="$PROJECT_ID" \
            --quiet
    fi

    DB_HOST_IP=$(gcloud sql instances describe "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --format="value(ipAddresses[0].ipAddress)")

    pip3 install pymysql --break-system-packages > /dev/null 2>&1 || true
    python3 setup_schema.py "$DB_HOST_IP"
}

handle_static_ip() {
    if ! gcloud compute addresses describe "$STATIC_IP_NAME" --region="$REGION" --project="$PROJECT_ID" > /dev/null 2>&1; then
        gcloud compute addresses create "$STATIC_IP_NAME" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --quiet
    fi

    DYNAMIC_IP=$(gcloud compute addresses describe "$STATIC_IP_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(address)")
}

handle_vm() {
    if ! gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --project="$PROJECT_ID" > /dev/null 2>&1; then
        gcloud compute instances create "$VM_NAME" \
            --project="$PROJECT_ID" \
            --zone="$ZONE" \
            --machine-type=e2-standard-2 \
            --address="$DYNAMIC_IP" \
            --metadata-from-file=startup-script=startup.sh,webserver-app=server.py \
            --scopes=https://www.googleapis.com/auth/cloud-platform \
            --tags=http-server \
            --quiet
    fi

    if ! gcloud compute firewall-rules describe default-allow-http --project="$PROJECT_ID" > /dev/null 2>&1; then
        gcloud compute firewall-rules create default-allow-http \
            --project="$PROJECT_ID" \
            --action=ALLOW \
            --rules=tcp:80 \
            --target-tags=http-server \
            --quiet
    fi
}

handle_cloud_sql
handle_static_ip
handle_vm
