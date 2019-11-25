# Version 3

FROM python:3.7

WORKDIR /app/

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install libxml2 libxslt1.1

RUN apt-get clean autoclean \
    && apt-get autoremove --yes \
    && rm -rf /var/lib/{apt,dpkg,cache,log}/

RUN pip install beautifulsoup4 lxml unidecode

CMD ["/bin/bash"]
