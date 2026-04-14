#!/bin/bash

# Stop Metabase

echo "🛑 Stopping Metabase..."
podman stop metabase 2>/dev/null
podman rm metabase 2>/dev/null
echo "✅ Metabase stopped"
