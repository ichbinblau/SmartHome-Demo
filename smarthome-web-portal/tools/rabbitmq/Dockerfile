FROM ubuntu:16.04

ARG http_proxy

ARG https_proxy

ENV http_proxy ${http_proxy}

ENV https_proxy ${https_proxy}

ENV RABBITMQ_USER admin 

ENV RABBITMQ_PASSWORD admin

# Uncomment the two lines below if you wish to use an Ubuntu mirror repository
# that is closer to you (and hence faster). The 'sources.list' file inside the
# 'tools/docker/' folder is set to use one of Ubuntu's official mirror in Taiwan.
# You should update this file based on your own location. For a list of official
# Ubuntu mirror repositories, check out: https://launchpad.net/ubuntu/+archivemirrors
COPY sources.list /etc/apt
RUN rm /var/lib/apt/lists/* -vf

RUN apt-get clean && apt-get update

# install rabbitmq-server and add admin user
RUN apt-get install -y --no-install-recommends rabbitmq-server 

ENV PATH /usr/lib/rabbitmq/bin:$PATH

# set home so that any `--user` knows where to put the erlang cookie
ENV HOME /var/lib/rabbitmq

RUN mkdir -p /var/lib/rabbitmq /etc/rabbitmq \
    && chown -R rabbitmq:rabbitmq /var/lib/rabbitmq /etc/rabbitmq \
    && chmod -R 777 /var/lib/rabbitmq /etc/rabbitmq

# add a symlink to the .erlang.cookie in /root so we can "docker exec rabbitmqctl ..." without gosu
RUN ln -sf /var/lib/rabbitmq/.erlang.cookie /root/

#RUN ln -sf /usr/lib/rabbitmq/lib/rabbitmq_server-$RABBITMQ_VERSION/plugins /plugins

# install rabbitmq management portal
RUN rabbitmq-plugins enable --offline rabbitmq_management

EXPOSE 5672 15672

ADD init_mq.sh /init_mq.sh

RUN chmod +x /init_mq.sh

CMD ["/init_mq.sh"]
