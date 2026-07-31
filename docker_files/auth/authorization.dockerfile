FROM iep-base:1.0

RUN mkdir -p /opt/src/auth
RUN mkdir -p /opt/src/shared

WORKDIR /opt/src

COPY src/auth/application.py ./auth/application.py
COPY src/auth/api_endpoints.py ./auth/api_endpoints.py
COPY src/auth/configuration.py ./auth/configuration.py
COPY src/auth/models.py ./auth/models.py
COPY src/shared/credential_decorators.py ./shared/credential_decorators.py

ENV PYTHONPATH=.

ENTRYPOINT ["python", "./auth/application.py"]