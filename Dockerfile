FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pdm

COPY pyproject.toml pdm.lock /app/

ENV PDM_USE_VENV=true
ENV PDM_VENV_IN_PROJECT=true 
ENV PATH="/app/.venv/bin:$PATH"

RUN pdm install --prod --frozen-lock  && \
    # find /app/.venv -name "*.pyc" -exec rm -f {} \; && \
    # find /app/.venv -name "*.dist-info" -exec rm -rf {} \; && \
    echo "install successful"

# RUN pdm use -f /app/.venv
RUN pdm use -f $(which python3.11)

COPY . /app

RUN du -sh /app/.venv && echo "Venv size printed"

CMD ["pdm", "run", "main.py"]
# FROM python:3.11-slim AS final

# WORKDIR /app

# COPY --from=builder /app/.venv /app/.venv

# ENV PDM_USE_VENV=true
# ENV PDM_VENV_IN_PROJECT=true 
# ENV PATH="/app/.venv/bin:$PATH"
# CMD ["/app/.venv/bin/python", "main.py"]

# FROM python:3.11-slim

# WORKDIR /app

# RUN pip install --no-cache-dir --upgrade pip && \
#     pip install --no-cache-dir pdm

# COPY pyproject.toml pdm.lock /app/

# ENV PDM_USE_VENV=true
# ENV PDM_VENV_IN_PROJECT=true 
# ENV PATH="/app/.venv/bin:$PATH"

# RUN pdm install --prod --frozen-lock && echo "install successful"

# COPY . /app

# RUN du -sh /app/.venv && echo "Venv size printed"

# CMD ["pdm", "run", "main.py"]

# podman buildx build --platform linux/amd64,linux/arm64 -t h.nodestaking.com/mlx/mnist:1 .
# podman buildx build --platform linux/amd64,linux/arm64 -t h.nodestaking.com/mlx/mnist:1 --load .