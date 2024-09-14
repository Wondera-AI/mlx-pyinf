ARG BASE_IMAGE=nvidia/cuda:12.2.2-base-ubuntu22.04
FROM ${BASE_IMAGE}

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3.11-dev curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.11 get-pip.py && \
    pip install --no-cache-dir toml-to-requirements

COPY pyproject.toml /app/

RUN toml-to-req --toml-file pyproject.toml

RUN pip install --no-cache-dir -r requirements.txt

RUN sed -i '/torch/d' requirements.txt && \
    sed -i '/torchvision/d' requirements.txt && \
    sed -i '/torchaudio/d' requirements.txt

RUN pip install --no-cache-dir torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu122

RUN echo 'import torch; print(f"CUDA Available: {torch.cuda.is_available()}"); print(f"CUDA Devices: {torch.cuda.device_count()}")' > test_cuda.py && \
    python3.11 test_cuda.py && \
    rm test_cuda.py

COPY main.py /app/main.py
COPY src/ /app/src/

RUN find /app/src/ -name "*.pyc" -exec rm -f {} \;

ENV PYTHONUNBUFFERED=1

CMD ["python3.11", "main.py"]


## PDM VERSION BELOW - LESSON: PDM ONLY A DEV TOOL

# ARG BASE_IMAGE=nvidia/cuda:12.2.2-base-ubuntu22.04
# ARG PYTHON_BASE=python:3.11-slim

# # --------------- Build Stage ---------------
# FROM ${PYTHON_BASE} AS builder

# WORKDIR /app

# RUN pip install --no-cache-dir pdm

# COPY pyproject.toml pdm.lock /app/

# ENV PATH="/app/.venv/bin:$PATH"

# RUN pdm use -f $(which python3.11)

# RUN mkdir -p /tmp/pdm_cache && \
#     export PDM_CACHE_DIR=/tmp/pdm_cache && \
#     pdm install --prod --frozen-lock && \
#     rm -rf /tmp/pdm_cache && \
#     find /app/.venv -name "*.pyc" -exec rm -f {} \; && \
#     echo "install successful"

# # --------------- Final Stage ---------------
# FROM ${BASE_IMAGE} AS final

# WORKDIR /app

# ENV DEBIAN_FRONTEND=noninteractive

# RUN apt-get update && \
#     apt-get install -y curl software-properties-common && \
#     add-apt-repository ppa:deadsnakes/ppa && \
#     apt-get update && \
#     apt-get install -y python3.11 && \
#     echo "Python 3.11 Installed" && \
#     curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.11 get-pip.py && \
#     echo "Pip Installed"

# COPY --from=builder /app/.venv /app/.venv

# RUN du -sh /app/.venv && \
#     echo "Venv Size" && \ 
#     ln -sf /usr/bin/python3.11 /app/.venv/bin/python  && \
#     echo "Python Linked" && \
#     ln -sf /usr/local/bin/pip /app/.venv/bin/pip && \
#     echo "Pip Linked" && \
#     /app/.venv/bin/pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu122 && \
#     echo "Pytorch Installed"

# RUN echo 'import torch; print(f"CUDA Available: {torch.cuda.is_available()}"); print(f"CUDA Devices: {torch.cuda.device_count()}")' > test_cuda.py && \
#     /app/.venv/bin/python3 test_cuda.py && \
#     rm test_cuda.py

# COPY main.py /app/main.py
# COPY src/ /app/src/

# # final image cleanups
# RUN find /app/src/ -name "*.pyc" -exec rm -f {} \;

# ENV PYTHONUNBUFFERED=1

# CMD [".venv/bin/python3", "main.py"]


# # # Install Python 3.11 and pip
# RUN apt-get update && apt-get install -y \
# python3.11 \
# python3.11-venv \
# python3-pip \
# curl && \
# rm -rf /var/lib/apt/lists/*

# # Install PyTorch and necessary dependencies
# RUN curl -s https://bootstrap.pypa.io/get-pip.py | python3.11 && \
# pip install --no-cache-dir torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu122
