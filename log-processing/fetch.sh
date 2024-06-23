#!/bin/bash


CILIUM_POD="cilium-qbj7k"  # Change this to the actual pod name 
NAMESPACE="kube-system"
LOCAL_LOG_FILE="fetched_events.log"
LAST_POSITION_FILE="last_position.txt"

# Ensure the local files exists
touch $LOCAL_LOG_FILE
touch $LAST_POSITION_FILE

# Function to fetch logs from the Cilium pod
fetch_logs() {
    # Get the current size of the remote log file
    CURRENT_SIZE=$(kubectl exec -n $NAMESPACE $CILIUM_POD -- stat -c %s /var/run/cilium/hubble/events.log)
    
    # Read the last known size of the remote log file
    if [[ -f $LAST_POSITION_FILE ]]; then
        LAST_POSITION=$(cat $LAST_POSITION_FILE)
    else
        LAST_POSITION=0
    fi
    
    # If the log file has grown, fetch the new entries
    if (( CURRENT_SIZE > LAST_POSITION )); then
        # Calculate the number of bytes to read
        BYTE_COUNT=$((CURRENT_SIZE - LAST_POSITION))
        
        # Fetch the new logs and append them to the local log file
        kubectl exec -n $NAMESPACE $CILIUM_POD -- tail -c +$((LAST_POSITION + 1)) /var/run/cilium/hubble/events.log | head -c $BYTE_COUNT >> $LOCAL_LOG_FILE
        
        # Update the last position
        echo $CURRENT_SIZE > $LAST_POSITION_FILE
    fi
}

# Fetch logs every 5 seconds
while true; do
    fetch_logs
    sleep 5
done