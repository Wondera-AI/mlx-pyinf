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

# Lock dependencies for different platforms
RUN pdm lock --platform=manylinux_2_36_aarch64 --python="==3.11.*" && \
    pdm lock --platform=macos_arm64 --python="==3.11.*" --append

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
