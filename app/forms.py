from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired
from app.models import User, School

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('supervisor', 'Supervisor')], validators=[DataRequired()])
    submit = SubmitField('Create User')

class SchoolForm(FlaskForm):
    name = StringField('School Name', validators=[DataRequired()])
    required_hours = IntegerField('Required Hours', validators=[DataRequired()])
    submit = SubmitField('Add School')

class AssignmentForm(FlaskForm):
    user = SelectField('Supervisor', coerce=int, validators=[DataRequired()])
    school = SelectField('School', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign School')

    def __init__(self, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        self.user.choices = [(u.id, u.username) for u in User.query.filter_by(role='supervisor').all()]
        self.school.choices = [(s.id, f"{s.name} ({s.required_hours} hrs)") for s in School.query.all()]

class AssignFromPoolForm(FlaskForm):
    user_id = IntegerField('User ID', validators=[DataRequired()])
    hours = IntegerField('Hours to Assign', validators=[DataRequired()])
    submit = SubmitField('Assign from Pool')