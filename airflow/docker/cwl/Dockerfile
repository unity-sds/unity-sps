# docker:dind Dockerfile: https://github.com/docker-library/docker/blob/master/Dockerfile-dind.template
# FROM docker:dind
FROM docker:25.0.3-dind

# install Python
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN apk add gcc musl-dev linux-headers python3-dev
RUN apk add --no-cache python3 py3-pip
RUN apk add vim

# install CWL libraries
RUN mkdir /usr/share/cwl \
    && cd /usr/share/cwl \
    && python -m venv venv \
    && source venv/bin/activate \
    && pip install cwltool cwl-runner docker boto3 awscli

# install nodejs to parse Javascript in CWL files
RUN apk add --no-cache nodejs npm

# script to execute a generic CWL workflow with arguments
COPY docker_cwl_entrypoint.sh /usr/share/cwl/docker_cwl_entrypoint.sh

WORKDIR /usr/share/cwl
ENTRYPOINT ["/usr/share/cwl/docker_cwl_entrypoint.sh"]
