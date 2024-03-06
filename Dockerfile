# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a new user 'mhmd' and switch to it
RUN adduser --disabled-password --gecos '' mhmd 

RUN chown -R mhmd:mhmd /usr/src/app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libffi-dev \
    python3-dev \
    graphviz libgraphviz-dev pkg-config\
    gcc \
    gfortran \
    libopenblas-dev \
    liblapack-dev && rm -rf /var/lib/apt/lists/*

# Install Pipenv
RUN pip install pipenv

# Copy the Pipfile and Pipfile.lock into the container at /usr/src/app
COPY Pipfile Pipfile.lock ./

# Install dependencies in a virtual environment
RUN pipenv install --deploy --ignore-pipfile \
    && pipenv install spacy \
    && pipenv run python -m spacy download en_core_web_sm \
    && pipenv run python -m nltk.downloader stopwords \
    && pipenv run python -m nltk.downloader wordnet

# Copy the rest of your application's code
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run your app using Pipenv's virtual environment
CMD ["pipenv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
# CMD ["pipenv", "run", "gunicorn", "dj.wsgi:application", "--bind", "0.0.0.0:8000"]
