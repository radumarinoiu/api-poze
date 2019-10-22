FROM ubuntu
RUN apt-get update &&\
    apt-get -y install python3 python3-pip &&\
    python3 -m pip install bson pymongo requests imgurpython flask
ADD . /usr/local/server
