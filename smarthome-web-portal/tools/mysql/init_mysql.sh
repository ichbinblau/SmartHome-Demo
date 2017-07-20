#!/bin/bash

echo $MYSQL_ROOT_PASSWORD
echo $MYSQL_REPL_PASSWORD
echo $ROLE
echo $MARIADB_MASTER_SERVICE_HOST
DATADIR=/var/lib/mysql
MYSQLCNF=/etc/mysql/mariadb.conf.d/50-server.cnf

if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
    echo "Error: database is uninitialized and password option is not given"
    exit 1
else
    if [ -z "$MYSQL_REPL_PASSWORD" ]; then
        echo "Warning: password for the replication user is not given. Use root's password by default"
        MYSQL_REPL_PASSWORD=$MYSQL_ROOT_PASSWORD
    fi
fi

# setup server id for mysql server
if [ ! -z "$ROLE" ]; then
    if [ "$ROLE" == "Master" ] || [ "$ROLE" == "M" ] || [ "$ROLE" == "MASTER" ] || [ "$ROLE" == "master" ]; then
        #sed -i '/\[mysqld\]/a server-id=1\nlog-bin\nauto_increment_increment=2\nauto_increment_offset=1\nbinlog_do_db=smart_home\nbinlog_ignore_db=mysql' $MYSQLCNF
        sed -i '/\[mysqld\]/a server-id=1\nlog-bin\nbinlog_do_db=smart_home\nbinlog_ignore_db=mysql' $MYSQLCNF
        ROLE="M"
    elif [ "$ROLE" == "Slave" ] || [ "$ROLE" == "S" ] || [ "$ROLE" == "SLAVE" ] || [ "$ROLE" == "slave" ]; then 
        #sed -i '/\[mysqld\]/a server-id=2\nlog-bin\nauto_increment_increment=2\nauto_increment_offset=2\nbinlog_do_db=smart_home\nbinlog_ignore_db=mysql' $MYSQLCNF
        sed -i '/\[mysqld\]/a server-id=2\nlog-bin\nbinlog_do_db=smart_home\nbinlog_ignore_db=mysql' $MYSQLCNF
        ROLE="S"
    else
        echo "Error: database role is invalid"
        echo "Set environment variable ROLE as Master or Slave" 
        exit 1
    fi
else
    echo "Error: database role is not specified"
    echo "Set environment variable ROLE as Master or Slave"
    exit 1
fi

# initialize db
rm -fr $DATADIR/*
/usr/bin/mysql_install_db --datadir=/var/lib/mysql --rpm
/usr/bin/mysqld_safe --skip-networking > /dev/null 2>&1 &

for i in {30..0}; do
    if ! mysql -uroot -e "select 1" &>/dev/null; then
        sleep 1
    else
        echo "MySQL process is up"
        break
    fi
done

if [ "$i" = 0 ]; then
    echo 'MySQL init process failed'
    exit 1
fi

#UPDATE user SET plugin='mysql_native_password', password=PASSWORD('$MYSQL_ROOT_PASSWORD') WHERE user='root';
# setup root password
if [ "$ROLE" == "M" ]; then
mysql -uroot <<EOF
CREATE USER 'root'@'%' IDENTIFIED VIA mysql_native_password; 
SET PASSWORD FOR 'root'@'%'=PASSWORD('$MYSQL_ROOT_PASSWORD');
GRANT ALL ON *.* TO 'root'@'%' WITH GRANT OPTION;
DROP DATABASE IF EXISTS test;
FLUSH PRIVILEGES;
EOF
fi

echo "Setting up repl user"
# setup mysql repliation account
#GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%' IDENTIFIED BY '$MYSQL_REPL_PASSWORD';
if [ "$ROLE" == "M" ]; then
mysql -uroot -p$MYSQL_ROOT_PASSWORD <<EOF 
CREATE USER 'repl'@'%' IDENTIFIED VIA mysql_native_password;
SET PASSWORD FOR 'repl'@'%'=PASSWORD('$MYSQL_REPL_PASSWORD');
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%' IDENTIFIED BY '$MYSQL_REPL_PASSWORD';
FLUSH PRIVILEGES ;
EOF
else
mysql -uroot -p$MYSQL_ROOT_PASSWORD <<EOF
STOP SLAVE;
CHANGE MASTER TO master_host='$MYSQL_MASTER_SERVICE_HOST', master_user='repl', master_password='$MYSQL_REPL_PASSWORD';
START SLAVE;
EOF
fi

# kill mysqld 
if ! mysqladmin -uroot -p$MYSQL_ROOT_PASSWORD shutdown > /dev/null; then
    echo 'MySQL init process failed'
    exit 1
fi

echo
echo "Mysql server has been initialized"
echo

exec "$@"
