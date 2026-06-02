#!/bin/bash
echo "Testing if system_config table exists in database (RED phase)..."

# Wait a bit for DB to be up if just started
sleep 2

# Execute psql inside the db container
docker exec master-db-1 psql -U postgres -d replayme_db -c "SELECT * FROM system_config;" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "ERROR: Table system_config exists. Test failed (it should not exist in RED phase)."
    exit 1
else
    echo "SUCCESS: Query failed, table system_config does not exist as expected."
    exit 0
fi
