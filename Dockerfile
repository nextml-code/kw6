FROM python:3.8

WORKDIR /usr/src/kw6

SHELL [ "/bin/bash", "-c" ]

RUN pip install virtualenv==20.0.16
RUN virtualenv venv -p python3.8

COPY requirements.txt ./

RUN virtualenv venv \
    && source venv/bin/activate \
    && pip install --requirement requirements.txt \
    && pip install pytest

COPY .git/ ./.git/
COPY setup.* ./
COPY pytest.ini ./
COPY README.rst ./
COPY LICENSE ./
COPY kw6/ ./kw6

RUN source venv/bin/activate \
    && pip install . \
    && python -c "import kw6"

RUN echo 'source venv/bin/activate' > ~/.bashrc

ENTRYPOINT [ "/bin/bash", "-i" ]
