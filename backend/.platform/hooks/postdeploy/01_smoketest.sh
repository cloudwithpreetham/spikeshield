#!/bin/bash
sleep 2
if ! curl -s --fail http://127.0.0.1:8000/health > /dev/null; then
    echo "Smoke test /health failed" >> /var/log/eb-hooks.log
    exit 1
fi
echo "Smoke test passed" >> /var/log/eb-hooks.log
exit 0
