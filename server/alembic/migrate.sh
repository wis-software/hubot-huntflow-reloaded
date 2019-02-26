#!/bin/bash
ALEMBIC_PATH="$(which alembic)"
export POSTGRES_URL=${POSTGRES_URL="$1"}
env PYTHONPATH=$(pwd) ${ALEMBIC_PATH} upgrade head
