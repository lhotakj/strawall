set -e

PY=$(python3 --version)
PORT=5000
GUNICORN_THREADS=3
GUNICORN_WORKERS=1

echo "Exposing Gunicorn on port ${PORT} ..."
echo "APPLICATION_ROOT: ${APPLICATION_ROOT}"
echo "GUNICORN_WORKERS: ${GUNICORN_WORKERS}"
echo "GUNICORN_THREADS: ${GUNICORN_THREADS}"
echo "PYTHON:           ${PY}"

gunicorn --bind 0.0.0.0:${PORT} --threads="${GUNICORN_THREADS}" --workers="${GUNICORN_WORKERS}" app:app