FROM iep-base:1.0

RUN mkdir -p /opt/src/auth
WORKDIR /opt/src/auth

COPY src/auth/migrate.py ./migrate.py
COPY src/auth/configuration.py ./configuration.py
COPY src/auth/models.py ./models.py

ENTRYPOINT ["python", "./migrate.py"]
