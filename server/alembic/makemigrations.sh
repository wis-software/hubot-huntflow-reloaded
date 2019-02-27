#!/bin/bash
ALEMBIC_PATH="$(dirname "$(which python)" )/alembic"
export POSTGRES_URL=${POSTGRES_URL="$2"}
env PYTHONPATH=$(pwd) ${ALEMBIC_PATH} revision --autogenerate -m $1
