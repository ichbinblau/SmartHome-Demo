#!/bin/bash
# The script is to let the process wait until the dependency process starts up.

MYSQL_ROOT_PASSWORD=intel123

function wait_service()
{
    # The func is to run command for at most 30 times until it returns success code
    # $1: the command to run
    # $2: the service which depends on the command's success return
    # $3: the dependent service name
    for i in {30..0}; do
        eval $1
        if [[ $? != 0 ]]; then
            sleep 1
        else
            echo "[$2]: process $3 started."
            break
        fi
    done
    if [ "$i" = 0 ]; then
        echo "[$2]: $3 process failed to start."
        exit 1
    fi
}

function wait_for_rabbitmq()
{
    wait_service "/etc/init.d/rabbitmq-server status &>/dev/null" $1 "rabbitmq"
}

function wait_for_mysql()
{
    wait_service "/usr/bin/mysqladmin -uroot -p$MYSQL_ROOT_PASSWORD --protocol=tcp ping &>/dev/null" $1 "mysql"
}

function wait_for_home()
{
    wait_service "/usr/bin/pgrep -lf SHProject &>/dev/null" $1 "home-portal"
}

function start_mysql()
{
    # initialize mysql server
    /usr/sbin/mysqld --initialize --user=mysql 
    
    # start mysql in safe mode
    /usr/bin/mysqld_safe --skip-networking > /dev/null 2>&1 &
    
    # wait until mysql process is fully functional
    for i in {30..0}; do
        if ! mysql -uroot -e "select 1" &>/dev/null; then
            sleep 1
        else
            echo "[mysql]: mysql_safe process is up"
            break
        fi
    done
    if [ "$i" = 0 ]; then
        echo '[mysql]: mysql_safe process failed to start'
        exit 1
    fi

    # set root password, change mariadb root password plugin to mysql_native_password
    mysql -uroot <<EOF
update mysql.user set authentication_string=PASSWORD('$MYSQL_ROOT_PASSWORD'), plugin='mysql_native_password' where user='root';
flush privileges;
EOF
    # stop mysql process for initialization
    mysqladmin -uroot -p$MYSQL_ROOT_PASSWORD shutdown
    
    # start mysql server
    /usr/bin/pidproxy /var/run/mysqld/mysqld.pid /usr/bin/mysqld_safe
    
}

function start_service()
{
    case $1 in
        rabbitmq)
            wait_for_mysql $1
            echo "[rabbitmq]: starting $1 server."
            /usr/sbin/rabbitmq-server
            ;;
        celery-worker)
            wait_for_rabbitmq $1
            wait_for_home $1
            echo "[celery-worker]: starting $1 server."
            /usr/local/bin/celery -A CeleryTask.tasks purge -f
            sleep 3
            /usr/bin/python2.7 CeleryTask/tasks.py
            sleep 3
            /usr/local/bin/celery -A CeleryTask.celeryapp worker -l info
            ;;
        web-portal)
            wait_for_mysql $1
            echo "[web-portal]: starting $1 server."
            /usr/bin/python2.7 initial_db.py && /usr/bin/python2.7 SHProject.py
            ;;
        admin-portal)
            wait_for_home $1
            echo "[admin-portal]: starting $1 server." 
            /usr/bin/python2.7 tools/smarthome-admin-portal/run.py
            ;;
        mysql)
            echo "[mysql-server]: starting $1 server."
            start_mysql
            ;;         
        *)
            echo "Unknown service: $1."
            ;;
    esac
}

start_service $1
