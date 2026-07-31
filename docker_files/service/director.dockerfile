FROM iep-base:1.0

RUN mkdir -p /opt/src/auth
RUN mkdir -p /opt/src/shared
RUN mkdir -p /opt/src/service/shared
RUN mkdir -p /opt/src/service/director

WORKDIR /opt/src

COPY src/auth/models.py ./auth/models.py
COPY src/shared/credential_decorators.py ./shared/credential_decorators.py
COPY src/service/shared/configuration.py ./service/shared/configuration.py
COPY src/service/shared/models.py ./service/shared/models.py
COPY src/service/shared/blockchain.py ./service/shared/blockchain.py
COPY src/service/shared/contracts ./service/shared/contracts
COPY src/service/director/application.py ./service/director/application.py
COPY src/service/director/api_endpoints.py ./service/director/api_endpoints.py

ENV PYTHONPATH=.

ENTRYPOINT ["python", "./service/director/application.py"]
