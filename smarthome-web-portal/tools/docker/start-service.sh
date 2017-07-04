#!/bin/bash
# The script is to let the process wait until the dependency process starts up.

function wait_service()
{
    # Wait until the service gets started.
    while ! /bin/netstat -an | grep $2 >/dev/null; do
        echo "Waiting for $1 to start ..."
        sleep 1
    done
    echo "$1 started."
}

function start_service()
{
    case $1 in
        rabbitmq)
            wait_service 'MySQL' '3306'
            echo "Starting $1 server."
            /usr/sbin/rabbitmq-server
            ;;
        celery-worker)
            wait_service 'MySQL' '3306'
            wait_service 'Rabbitmq' '5672'
            echo "Starting $1 server."
            sleep 3
            /usr/local/bin/celery -A CeleryTask.tasks purge -f
            sleep 3
            /usr/bin/python2.7 CeleryTask/tasks.py
            sleep 3
            /usr/local/bin/celery -A CeleryTask.celeryapp worker -l info
            ;;
        web-portal)
            wait_service 'MySQL' '3306'
            /usr/bin/python2.7 initial_db.py
            /usr/bin/python2.7 SHProject.py
            ;;
        *)
            echo "Unknown service: $1."
            ;;
    esac
}

start_service $1
