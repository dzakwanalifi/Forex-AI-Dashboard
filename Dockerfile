# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install uv
RUN pip install uv

# Install any needed packages specified in requirements.txt using uv
RUN uv pip install -r requirements.txt

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

# Install JavaScript dependencies and build assets
RUN npm install
RUN npm run build

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run app.py when the container launches
CMD ["flask", "run"]
