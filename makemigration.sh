#!/usr/bin/env sh

alembic revision -m "$1"

expand_head=$(alembic show head | head -n 1 | cut -d' ' -f 2)

DIR=$(dirname "$0")
echo "$expand_head" > $DIR/db/MIGRATIONS_HEAD
