#
# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

FROM ubuntu:16.04

ARG http_proxy

ARG https_proxy

ENV http_proxy ${http_proxy}

ENV https_proxy ${https_proxy}

RUN echo $https_proxy

RUN echo $http_proxy

# Uncomment the two lines below if you wish to use an Ubuntu mirror repository
# that is closer to you (and hence faster). The 'sources.list' file inside the
# 'tools/docker/' folder is set to use one of Ubuntu's official mirror in Taiwan.
# You should update this file based on your own location. For a list of official
# Ubuntu mirror repositories, check out: https://launchpad.net/ubuntu/+archivemirrors
#COPY tools/docker/sources.list /etc/apt
#RUN rm /var/lib/apt/lists/* -vf

RUN apt-get clean && apt-get update

# install python2 and common tools
RUN apt-get -y install netcat python

# forward port
EXPOSE 3000 4000

# Install MySQL Server in a Non-Interactive mode. Default root password will be "intel123"
RUN apt-get install -y debconf-utils \
    && echo "mysql-server mysql-server/root_password password intel123" | debconf-set-selections \
    && echo "mysql-server mysql-server/root_password_again password intel123" | debconf-set-selections \
    && apt-get -y install mysql-server \
    && sed -i -e"s/^bind-address\s*=\s*127.0.0.1/bind-address = 0.0.0.0/" /etc/mysql/my.cnf \
    && mkdir -p /var/run/mysqld \
    && chown mysql:mysql /var/run/mysqld

# Install rabbitmq supervisor and python deps for data analytics
RUN apt-get install -y rabbitmq-server python-pip supervisor python-scipy python-numpy python-matplotlib

# Install source code
COPY . /opt/SmartHome-Demo/smarthome-web-portal/

COPY tools/docker/web-portal.conf /etc/supervisor/conf.d/web-portal.conf
COPY tools/docker/start-service.sh /opt/SmartHome-Demo/smarthome-web-portal/start-service.sh

WORKDIR /opt/SmartHome-Demo/smarthome-web-portal

# install portal dependencies
RUN pip install -r requirements.txt

# create symbolic link to admin portal's model images from the home portal
RUN ln -sf /opt/SmartHome-Demo/smarthome-web-portal/tools/smarthome-admin-portal/admin/static/images/model /opt/SmartHome-Demo/smarthome-web-portal/static/image/model 

# configure portal settings
COPY tools/docker/SHProject.conf utils/SHProject.conf
COPY tools/docker/utils.py tools/smarthome-admin-portal/admin/utils.py

# unset proxy
ENV http_proxy ""
ENV https_proxy ""

ENV PYTHONPATH $PYTHONPATH:/opt/SmartHome-Demo/smarthome-web-portal

# start supervisor
CMD ["/usr/bin/supervisord", "-n"]

