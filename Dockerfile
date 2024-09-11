ARG BASE_IMAGE=nvidia/cuda:12.2.2-base-ubuntu22.04
ARG PYTHON_BASE=python:3.11-slim

# --------------- Build Stage ---------------
FROM ${PYTHON_BASE} AS builder

WORKDIR /app

RUN pip install --no-cache-dir pdm

COPY pyproject.toml pdm.lock /app/

ENV PATH="/app/.venv/bin:$PATH"

RUN pdm use -f $(which python3.11)

RUN mkdir -p /tmp/pdm_cache && \
    export PDM_CACHE_DIR=/tmp/pdm_cache && \
    pdm install --prod --frozen-lock && \
    rm -rf /tmp/pdm_cache && \
    find /app/.venv -name "*.pyc" -exec rm -f {} \; && \
    echo "install successful"

# --------------- Final Stage ---------------
FROM ${BASE_IMAGE} AS final

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y curl software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.11 && \
    echo "Python 3.11 Installed" && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.11 get-pip.py && \
    echo "Pip Installed"

COPY --from=builder /app/.venv /app/.venv

RUN du -sh /app/.venv && \
    echo "Venv Size" && \ 
    ln -sf /usr/bin/python3.11 /app/.venv/bin/python  && \
    echo "Python Linked" && \
    ln -sf /usr/local/bin/pip /app/.venv/bin/pip && \
    echo "Pip Linked" && \
    /app/.venv/bin/pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu122 && \
    echo "Pytorch Installed"

COPY main.py /app/main.py
COPY src/ /app/src/

# final image cleanups
RUN find /app/src/ -name "*.pyc" -exec rm -f {} \;

ENV PYTHONUNBUFFERED=1

CMD [".venv/bin/python3", "main.py"]


# ARG BASE_IMAGE=nvidia/cuda:11.3.1-base-ubuntu20.04
# ARG PYTHON_BASE=python:3.11-slim

# FROM ${BASE_IMAGE} AS builder
# # --build-arg BASE_IMAGE=python:3.11-slim

# WORKDIR /app

# RUN apt-get update && \
#     apt-get install -y python3 python3-pip

# RUN pip3 install --no-cache-dir --upgrade pip && \
#     pip3 install --no-cache-dir pdm

# COPY pyproject.toml pdm.lock /app/

# ENV PATH="/app/.venv/bin:$PATH"

# RUN pdm use -f $(which python3.11)

# RUN mkdir -p /tmp/pdm_cache && \
#     export PDM_CACHE_DIR=/tmp/pdm_cache && \
#     pdm install --prod --frozen-lock && \
#     rm -rf /tmp/pdm_cache && \
#     find /app/.venv -name "*.pyc" -exec rm -f {} \; && \
#     echo "install successful"

# COPY . /app

# RUN du -sh /app/.venv && echo "Venv size printed"

# CMD [".venv/bin/python3", "main.py"]


# # Set the base image to use, allowing for GPU support in the final stage


# RUN pip3 install --no-cache-dir torch torchvision torchaudio

# ARG BASE_IMAGE=nvidia/cuda:11.3.1-base-ubuntu20.04
# FROM ${BASE_IMAGE} AS builder
# # --build-arg BASE_IMAGE=python:3.11-slim

# WORKDIR /app

# RUN apt-get update && \
#     apt-get install -y python3 python3-pip

# RUN pip3 install --no-cache-dir --upgrade pip && \
#     pip3 install --no-cache-dir pdm

# COPY pyproject.toml pdm.lock /app/

# # ENV PDM_USE_VENV=true
# # ENV PDM_VENV_IN_PROJECT=true 
# ENV PATH="/app/.venv/bin:$PATH"

# RUN pdm use -f $(which python3.11)

# RUN mkdir -p /tmp/pdm_cache && \
#     export PDM_CACHE_DIR=/tmp/pdm_cache && \
#     pdm install --prod --frozen-lock && \
#     rm -rf /tmp/pdm_cache && \
#     find /app/.venv -name "*.pyc" -exec rm -f {} \; && \
#     echo "install successful"

# COPY . /app

# RUN du -sh /app/.venv && echo "Venv size printed"

# CMD [".venv/bin/python3", "main.py"]

# # FROM nvidia/cuda:12.6.1-cudnn-devel-ubuntu22.04 AS final
# # Use an argument to choose base image
# # ARG BASE_IMAGE=python:3.11-slim
# # FROM ${BASE_IMAGE} AS builder
# # --build-arg BASE_IMAGE=
# FROM python:3.11-slim AS builder

# WORKDIR /app

# # RUN apt-get update && \
# #     apt-get install -y python3-pip && \
# #     pip3 install --no-cache-dir pdm
# RUN pip install --no-cache-dir --upgrade pip && \
#     pip install --no-cache-dir pdm

# COPY pyproject.toml pdm.lock /app/

# ENV PDM_USE_VENV=true
# ENV PDM_VENV_IN_PROJECT=true 
# ENV PATH="/app/.venv/bin:$PATH"

# # RUN pdm use -f /app/.venv

# # RUN pdm install --prod --frozen-lock
# RUN mkdir -p /tmp/pdm_cache && \
#     export PDM_CACHE_DIR=/tmp/pdm_cache && \
#     pdm install --prod --frozen-lock && \
#     rm -rf /tmp/pdm_cache && \
#     # remove random crap in final stage
#     rm -rf /app/.git /app/.vscode && \
#     find /app -name "*.pyc" -exec rm -f {} \; && \
#     echo "Install successful"

# COPY . /app

# RUN du -sh /app/.venv && echo "Venv size printed"

# CMD ["pdm", "run", "main.py"]

# FROM nvidia/cuda:12.6.1-cudnn-devel-ubuntu22.04 AS final

# WORKDIR /app

# RUN apt-get update && apt-get install -y python3-pip

# RUN pip3 install --no-cache-dir pdm

# COPY pyproject.toml pdm.lock /app/

# ENV PDM_USE_VENV=true
# ENV PDM_VENV_IN_PROJECT=true

# ENV PATH="/app/.venv/bin:$PATH"

# RUN pdm install --prod --frozen-lock && \
#     rm -rf /tmp/pdm_cache && \
#     rm -rf /app/.git /app/.vscode && \
#     find /app -name "*.pyc" -exec rm -f {} \; && \
#     echo "Install successful"

# COPY . /app

# RUN du -sh /app/.venv && echo "Venv size printed"

# RUN pdm use -f $(which python3.11)

# CMD ["pdm", "run", "main.py"]


# RUN mkdir -p /tmp/pdm_cache && \
#     export PDM_CACHE_DIR=/tmp/pdm_cache && \
#     pdm install --prod --frozen-lock && \
#     rm -rf /tmp/pdm_cache && \
#     # remove random crap in final stage
#     rm -rf /app/.git /app/.vscode && \
#     find /app -name "*.pyc" -exec rm -f {} \; && \
#     echo "Install successful"


# RUN pdm use -f /app/.venv/bin/python3.11

# RUN rm -rf /app/.git /app/.vscode

# RUN du -sh /app/.venv && echo "Venv size printed"

# # Use a smaller base image (Debian-based slim image)
# FROM python:3.11-slim

# # Set up environment variables
# ENV PDM_HOME="/root/.pdm" \
#     PATH="$PATH:/root/.pdm/bin" \
#     PIP_NO_CACHE_DIR=1

# # # Install curl and PDM dependencies (Minimize the installation size)
# # RUN apt-get update && apt-get install -y --no-install-recommends \
# #     curl build-essential && \
# #     curl -sSL https://pdm-project.org/install-pdm.py | python3 - && \
# #     apt-get remove -y build-essential && \
# #     apt-get autoremove -y && \
# #     apt-get clean && \
# #     rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# # Copy only necessary project files
# WORKDIR /app
# COPY pyproject.toml pdm.lock /app/

# # Install project dependencies using PDM
# RUN pdm install --prod --frozen-lock

# # Copy the rest of the application code
# COPY . /app

# # Reduce the final image size by stripping unnecessary files
# RUN rm -rf /app/.pdm/venv/cache && rm -rf /app/.cache

# # Set the command to run the Python application
# CMD ["pdm", "run", "main.py"]

# ----

# FROM python:3.11-slim AS builder

# WORKDIR /app

# RUN pip install --no-cache-dir --upgrade pip && \
#     pip install --no-cache-dir pdm

# COPY pyproject.toml pdm.lock /app/

# ENV PDM_USE_VENV=true
# ENV PDM_VENV_IN_PROJECT=true 
# ENV PATH="/app/.venv/bin:$PATH"

# RUN pdm use -f 

# RUN mkdir -p /tmp/pdm_cache && \
#     export PDM_CACHE_DIR=/tmp/pdm_cache && \
#     pdm install --prod --frozen-lock && \
#     rm -rf /tmp/pdm_cache && \
#     find /app/.venv -name "*.pyc" -exec rm -f {} \; && \
#     echo "install successful"

# COPY . /app

# RUN du -sh /app/.venv && echo "Venv size printed"

# CMD ["pdm", "run", "main.py"]

# ---

# FROM python:3.11-slim AS final

# WORKDIR /app

# COPY --from=builder /app/.venv /app/.venv

# ENV PDM_USE_VENV=true
# ENV PDM_VENV_IN_PROJECT=true 
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