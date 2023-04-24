#!/usr/bin/env sh

set -e

case "$1" in
    api-local)
        exec python3 -m run_debug_server
        ;;
    api)
        exec berglas exec -- gunicorn -w ${GUNICORN_WORKERS:-1} -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${APP_HTTP_PORT:-8000} --access-logfile '-' svc.app:create_app
        ;;
    tests)
        exec pytest tests
        ;;
    analyze)
        echo "Run flake8"
        flake8 svc tests
        echo "Run bandit"
        bandit -r svc
        echo "Run safety"
        safety check -i 42194 || true
        echo "Run mypy"
        mypy svc --show-error-codes --ignore-missing-imports
        echo "Run black check"
        black --check svc
        echo "Run isort"
        isort --check-only --diff svc
        ;;
    *)
        exec "$@"
esac
