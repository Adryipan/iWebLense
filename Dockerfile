FROM debian:buster-slim
MAINTAINER SHING PONG ADRIAN YIP "spyip3@student.monash.edu"
RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev
RUN apt-get install -y libsm6 libxext6 libxrender-dev
WORKDIR /code
ADD iWebLens_server.py /code
COPY requirements.txt /code/requirements.txt
COPY yolov3-tiny.cfg /code/yolov3-tiny.cfg
COPY yolov3-tiny.weights /code/yolov3-tiny.weights
COPY coco.names /code/coco.names
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3" ]
CMD [ "/code/iWebLens_server.py" ]
