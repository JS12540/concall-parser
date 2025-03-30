# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only required files first (to leverage Docker caching)
COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false && poetry install --no-root --no-dev

# Copy the entire project
COPY . .

# Command to run the parser (modify this based on your project entry point)
CMD ["python", "-m", "parser"]
