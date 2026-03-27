set dotenv-load := true

image_name := env_var_or_default("IMAGE_NAME", "openprescribing-streamlit")
host_port := env_var_or_default("HOST_PORT", "8501")

default:
    @just --list

run:
    uv run streamlit run app.py

docker-build:
    #!/usr/bin/env bash
    set -euo pipefail

    docker build --tag "{{ image_name }}" .

docker-smoke:
    #!/usr/bin/env bash
    set -euo pipefail

    docker run --rm "{{ image_name }}" uv run python -c "import app"

docker-run:
    #!/usr/bin/env bash
    set -euo pipefail

    docker run --rm --publish "{{ host_port }}:8501" "{{ image_name }}"
