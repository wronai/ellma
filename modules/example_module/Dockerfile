# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in pyproject.toml
RUN pip install --no-cache-dir .

# Run tests when the container launches
CMD ["python", "-m", "pytest", "test.py", "-v"]
