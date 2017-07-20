FROM ubuntu:16.04

ARG http_proxy

ARG https_proxy

ENV http_proxy ${http_proxy}

ENV https_proxy ${https_proxy}

ENV DEBIAN_FRONTEND noninteractive

# Uncomment the two lines below if you wish to use an Ubuntu mirror repository
# that is closer to you (and hence faster). The 'sources.list' file inside the
# 'tools/docker/' folder is set to use one of Ubuntu's official mirror in Taiwan.
# You should update this file based on your own location. For a list of official
# Ubuntu mirror repositories, check out: https://launchpad.net/ubuntu/+archivemirrors
COPY sources.list /etc/apt
RUN rm /var/lib/apt/lists/* -vf

RUN apt-get clean && apt-get update

# RUN apt-get install -y debconf-utils \
RUN apt-get -q -y install mariadb-server \
    && sed -i -e "s/^bind-address\s*=\s*127.0.0.1/bind-address = 0.0.0.0/" /etc/mysql/mariadb.conf.d/50-server.cnf \
    && mkdir -p /var/run/mysqld /var/run/mysql \
    && chown mysql:mysql /var/run/mysqld /var/lib/mysql \
    && chmod 777 /var/run/mysqld

COPY init_mysql.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/init_mysql.sh 
ENTRYPOINT ["/usr/local/bin/init_mysql.sh"]

EXPOSE 3306
CMD ["mysqld"]
