FROM debian:stable

USER root

RUN apt-get update
RUN apt-get -y install locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9

RUN apt-get install -y python3 python3-pip
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools

RUN apt-get install -y git

RUN apt-get update && \
      apt-get -y install sudo

RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo

# GPIO
RUN apt-get install RPi.GPIO

# GPIO, I2C, Serial (for Python3.x)
RUN set -x &&\
    apt-get update && apt-get install -y\
        python3-rpi.gpio \
        i2c-tools \
        python3-smbus \
        cu 

# WiringPi Install
RUN set -x &&\
    git clone https://github.com/WiringPi/WiringPi &&\
    cd WiringPi &&\
    ./build

# grove.py (for Python3.x pip)
RUN set -x &&\
    git clone https://github.com/Seeed-Studio/grove.py &&\
    cd grove.py/ &&\
    pip3 install .

# install python module
COPY requirements.txt .
RUN pip install -r requirements.txt --extra-index-url https://www.piwheels.org/simple
