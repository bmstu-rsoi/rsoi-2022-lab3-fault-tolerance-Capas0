FROM python:3.8-slim-buster

# create user
ENV APP_USER=rating
RUN useradd -ms /bin/bash $APP_USER

# create the appropriate directories
ENV APP_HOME=/app
RUN mkdir -p $APP_HOME && chown $APP_USER:$APP_USER -R $APP_HOME
WORKDIR $APP_HOME

# install python dependencies
COPY requirements.txt /tmp/
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# copy project
COPY --chown=$APP_USER:$APP_USER src/rating/ $APP_HOME/

# change to the app user
USER $APP_USER

# run app
CMD gunicorn --bind 0.0.0.0:$PORT manage:app
