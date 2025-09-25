from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(10), index=True) # 'admin' or 'supervisor'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True)
    required_hours = db.Column(db.Integer)

    def __repr__(self):
        return f'<School {self.name}>'

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=True)
    assigned_hours = db.Column(db.Integer)
    description = db.Column(db.String(100))

    user = db.relationship('User', backref=db.backref('assignments', lazy=True))
    school = db.relationship('School', backref=db.backref('assignments', lazy=True))

    def __repr__(self):
        if self.school:
            return f'<Assignment of {self.user.username} to {self.school.name}>'
        return f'<Assignment of {self.user.username} for {self.assigned_hours} hours>'

class UnusedHour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    hours = db.Column(db.Integer)

    school = db.relationship('School', backref=db.backref('unused_hours', lazy=True))

    def __repr__(self):
        return f'<Unused Hours for {self.school.name}: {self.hours}>'