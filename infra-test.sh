#!/bin/bash
echo "Testing port 8000 connectivity (RED phase)..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "ERROR: Port 8000 is accessible. Test failed (it should be refused in RED phase)."
    exit 1
else
    echo "SUCCESS: Connection refused on port 8000 as expected."
    exit 0
fi
