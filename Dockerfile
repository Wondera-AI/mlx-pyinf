FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pdm

COPY pyproject.toml pdm.lock /app/

COPY . /app

ENV PDM_USE_VENV=true
ENV PDM_VENV_IN_PROJECT=true 

ENV PATH="/app/.venv/bin:$PATH"

CMD pdm install --prod --frozen-lock && echo "install successful" && pdm run main.py

# podman buildx build --platform linux/amd64,linux/arm64 -t h.nodestaking.com/mlx/mnist:1 .
# podman buildx build --platform linux/amd64,linux/arm64 -t h.nodestaking.com/mlx/mnist:1 --load .