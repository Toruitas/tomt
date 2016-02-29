__author__ = 'Stuart'
#!usr/bin/venv python

import os
from app import create_app, db
from app.models import User, Role, Permission, Question, Answer
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('TOMT_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app,db)

def make_shell_context():
    return dict(app=app, db=db, User=User, Question=Question, Role=Role, Permission=Permission, Answer=Answer)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)  #python app.py db --help

@manager.command
def deploy():
    """
    Regardless of hosting method used, there are a series of tasks that must be carried out when an application is
    installed on a production server. Ex: Creation/update of DB tables. Having to run these tasks manually each time app
    is installed or upgraded is error prone and time consuming, so instead a command that performs all the req'd tasks
    can be added...

    These are all designed in a way that causes no problems if they are executed multiple times. Designing update funcs
    in this way makes it possible to run just this "deploy" command every time an installation or upgrade is done.

    heroku run python manage.py deploy

    memi14ab@student.cbs.dk
    :return:
    """
    """Run deployment tasks."""
    from flask.ext.migrate import upgrade
    from app.models import Role

    # migrate DB to latest revision
    upgrade()

    # create user roles
    Role.insert_roles()


if __name__=="__main__":
    manager.run()