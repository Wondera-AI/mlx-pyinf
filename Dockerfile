# Use an official Python runtime as a parent image
FROM python:3.11-slim
# FROM rayproject/ray:2.4.0

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install PDM
RUN pip install --upgrade pip && \
    pip install pdm && \
    echo "PDM installed successfully"

# Install dependencies using PDM
RUN pdm install && echo "Dependencies installed successfully"

# RUN ln -s $(pdm venv bin) /usr/local/bin/ray

# # Ensure Ray CLI is in PATH
# ENV PATH="/root/.local/bin:$PATH:/usr/local/bin"

# Define environment variable
# ENV NAME RayMlTrainJob
# ENV RAY_USAGE_STATS_ENABLED=1

# Run the application using PDM
CMD ["pdm", "run", "main.py"]
