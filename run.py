from app import app, db
from app.models import User
import click

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

@app.cli.command("init-db")
def init_db_command():
    """Creates the admin user."""
    if not User.query.filter_by(username='admin').first():
        print("Creating admin user...")
        admin_user = User(username='admin', role='admin')
        admin_user.set_password('123')
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")
