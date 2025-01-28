#!/bin/bash

catch() {
    echo "Import error occurred as resource likely already exists. Exiting gracefully to prevent errors."
    exit 0
}

if [ "$PRESERVE_ACTION" = "import" ]; then
    trap 'catch $?' ERR
    terraform import $BUCKET_RESOURCE $BUCKET_NAME
else
    terraform state rm $BUCKET_RESOURCE
fi
