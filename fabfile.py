from fabric.context_managers import cd, prefix
from fabric.operations import run, local, sudo
from fabric.state import env

environments = {
    "production": ('webapps', '185.22.184.145')
}


def deploy(project, host="production", packages=False, password=None, version=None):
    if host and host in environments:
        env.user, env.host_string = environments[host]
    if password is not None:
        env.password = password

    try:
        run("sudo stop %s" % project)
    except:
        print("%s is not running." % project)
    with cd('/home/webapps/%s' % project):
        run("git pull git@github.com:buremba/b2c.git")
        run("env/bin/python manage.py collectstatic --noinput --clear")
        if version is not None:
            run('echo "%s" > BUILD' % version)
        if packages:
            run("env/bin/pip install -r requirements.txt")
    run("sudo start %s" % project)
    # run("env/bin/gunicorn wsgi:application  -w 8 --bind 0.0.0.0:9000 --timeout 30")


def get_version(put_file=False):
    commit_count = local("git rev-list --count HEAD | xargs -n1 printf %04d", capture=True)
    commit_hash = local("git show --abbrev-commit HEAD | grep '^commit' | sed -e 's/commit //'", capture=True)
    version = "%s.%s" % (commit_count, commit_hash)
    if put_file:
        local("echo '%s' > VERSION" % version)
    return version


def gunicorn():
    local("gunicorn wsgi:application  -w 8 --bind 0.0.0.0:9000 --timeout 30")


def syncdb():
    run("python manage.py syncdb --all")


def create():
    run("python manage.py syncdb --all")
    run("cat ~/scripts/ege.sql | ./manage.py dbshell")
    run("cat ~/scripts/erp.sql | ./manage.py dbshell")
    local("echo 'project is successfully created'")


def clean():
    local('find . -name \*.pyc -delete')


def celery_start():
    local('celery worker --app=shop.celeryapp -E -B -l INFO')  # -B for beat


def createdb(db_name, port=5432, host="127.0.0.1"):
    run("createdb -p %s -h %s -E UTF-8 -e %s" % (host, port, db_name))