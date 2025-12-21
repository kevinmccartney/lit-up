#!/bin/sh

PORT=${1:-5890}
NETWORK=${2:-litup_local}

echo "🔍 Looking for Lambda containers on network '$NETWORK' with debug port $PORT..."

# Function to start port forwarding
start_forward() {
  CONTAINER_ID=$1
  CONTAINER_IP=$2
  PORT=$3
  echo "📡 Forwarding debug port from Lambda container $CONTAINER_ID ($CONTAINER_IP:$PORT) to host:$PORT"
  # Construct addresses
  ADDR1="TCP-LISTEN:${PORT},fork,reuseaddr"
  ADDR2="TCP:${CONTAINER_IP}:${PORT}"
  # Debug: show what we're about to pass to socat
  echo "DEBUG: About to run: socat '$ADDR1' '$ADDR2'"
  # Use function arguments to ensure proper quoting - call socat with exactly 2 args
  socat "$ADDR1" "$ADDR2" &
  SOCAT_PID=$!
  echo "✅ Port forwarding active (PID: $SOCAT_PID)"
}

while true; do
  # Find Lambda containers (SAM creates containers with names like sam-app-ConfigPostFunction-*)
  CONTAINER_IDS=$(docker ps --filter "network=$NETWORK" --filter "name=sam-app" --format "{{.ID}}" 2>/dev/null || echo "")
  
  if [ -n "$CONTAINER_IDS" ]; then
    for CONTAINER_ID in $CONTAINER_IDS; do
      CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CONTAINER_ID" 2>/dev/null || echo "")
      if [ -n "$CONTAINER_IP" ]; then
        # Check if socat is already running for this container
        if ! pgrep -f "socat.*$CONTAINER_IP:$PORT" >/dev/null; then
          start_forward "$CONTAINER_ID" "$CONTAINER_IP" "$PORT"
        fi
      fi
    done
  fi
  sleep 2
done
