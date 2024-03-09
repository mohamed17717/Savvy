FROM python:3.11

# Set the working directory in the container
WORKDIR /usr/src/realtime

# Copy the current directory contents into the container at /app
COPY ./ /usr/src/realtime

# Install any needed packages specified in requirements.txt
RUN pip install pipenv
RUN pipenv install --deploy --ignore-pipfile


# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["pipenv", "run", "uvicorn", "--reload", "main:app", "--host", "0.0.0.0", "--port", "8000"]
