# Use the official python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /usr/src/app

# Install FastAPI and Uvicorn
RUN pip install fastapi uvicorn

# Copy the application code to the container
COPY . .

# Command to run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]