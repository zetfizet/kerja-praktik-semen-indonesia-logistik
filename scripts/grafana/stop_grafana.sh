#!/bin/bash

# Stop Grafana

echo "🛑 Stopping Grafana..."
podman stop grafana 2>/dev/null
podman rm grafana 2>/dev/null
echo "✅ Grafana stopped"
