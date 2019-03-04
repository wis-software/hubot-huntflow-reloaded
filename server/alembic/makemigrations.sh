#!/bin/bash
ALEMBIC_PATH="$(which alembic)"
export POSTGRES_URL=${POSTGRES_URL="$2"}
env PYTHONPATH=$(pwd) ${ALEMBIC_PATH} revision --autogenerate -m $1
