# Use an official Python runtime as a parent image
FROM python:3.11-slim
# FROM rayproject/ray:2.4.0

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Install PDM and ensure it's in PATH
RUN pip install --upgrade pip && \
    pip install pdm && \
    echo "PDM installed successfully"

# # Lock dependencies for multiple platforms:
# # - x86_64 (the current platform)
# # - aarch64 (for ARM Linux)
# # - macOS arm64
# RUN pdm lock --platform=manylinux_2_36_x86_64 --python="==3.11.*" && \
#     pdm lock --platform=manylinux_2_36_aarch64 --python="==3.11.*" --append && \
#     pdm lock --platform=macos_arm64 --python="==3.11.*" --append

# Detect the platform and generate the lockfile only if it doesn't exist
RUN if [ ! -f "pdm.lock" ]; then \
    echo "Lockfile not found. Generating pdm.lock for the correct platform..."; \
    if [ "$(uname -m)" = "x86_64" ]; then \
        pdm lock --platform=manylinux_2_36_x86_64 --python="==3.11.*"; \
    elif [ "$(uname -m)" = "aarch64" ]; then \
        pdm lock --platform=manylinux_2_36_aarch64 --python="==3.11.*"; \
    elif [ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then \
        pdm lock --platform=macos_arm64 --python="==3.11.*"; \
    else \
        echo "Unsupported platform"; exit 1; \
    fi; \
fi

# Install dependencies using PDM and existing or newly generated lockfile
RUN pdm install --no-lock && echo "Dependencies installed successfully"

# # Install dependencies using PDM
RUN pdm install && echo "Dependencies installed successfully"

# RUN ln -s $(pdm venv bin) /usr/local/bin/ray

# # Ensure Ray CLI is in PATH
# ENV PATH="/root/.local/bin:$PATH:/usr/local/bin"

# Define environment variable
# ENV NAME RayMlTrainJob
# ENV RAY_USAGE_STATS_ENABLED=1

# Run the application using PDM
CMD ["pdm", "run", "main.py"]
