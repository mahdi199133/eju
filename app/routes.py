from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db
from app.forms import LoginForm, UserForm, SchoolForm, AssignmentForm, AssignFromPoolForm
from app.models import User, School, Assignment, UnusedHour
from urllib.parse import urlparse
from sqlalchemy import func

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
@app.route('/index')
@login_required
def index():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))

    form = AssignmentForm()

    # Calculate total assigned hours for each supervisor
    assigned_hours_subquery = db.session.query(
        Assignment.user_id,
        func.sum(Assignment.assigned_hours).label('total_hours')
    ).group_by(Assignment.user_id).subquery()

    supervisors = db.session.query(
        User,
        func.coalesce(assigned_hours_subquery.c.total_hours, 0).label('total_assigned_hours')
    ).outerjoin(
        assigned_hours_subquery, User.id == assigned_hours_subquery.c.user_id
    ).filter(User.role == 'supervisor').all()


    assignments = Assignment.query.all()
    unused_hours = UnusedHour.query.all()
    pool_form = AssignFromPoolForm()

    return render_template('index.html', title='Coordinator Dashboard', form=form, supervisors=supervisors, assignments=assignments, unused_hours=unused_hours, pool_form=pool_form)

@app.route('/assign_from_pool', methods=['POST'])
@login_required
def assign_from_pool():
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action.')
        return redirect(url_for('index'))

    form = AssignFromPoolForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        hours_to_assign = form.hours.data

        user = User.query.get(user_id)

        # Check total available hours in the pool
        total_pool_hours = db.session.query(func.sum(UnusedHour.hours)).scalar() or 0
        if hours_to_assign > total_pool_hours:
            flash(f'Not enough hours in the pool. Available: {total_pool_hours}')
            return redirect(url_for('index'))

        # Deduct hours from the pool
        remaining_to_deduct = hours_to_assign
        for unused_entry in UnusedHour.query.order_by(UnusedHour.id).all():
            if remaining_to_deduct == 0:
                break

            if unused_entry.hours >= remaining_to_deduct:
                unused_entry.hours -= remaining_to_deduct
                remaining_to_deduct = 0
                if unused_entry.hours == 0:
                    db.session.delete(unused_entry)
            else:
                remaining_to_deduct -= unused_entry.hours
                db.session.delete(unused_entry)

        # Create a new assignment
        assignment = Assignment(
            user_id=user.id,
            assigned_hours=hours_to_assign,
            description=f'Assigned from pool'
        )
        db.session.add(assignment)
        db.session.commit()
        flash(f'Assigned {hours_to_assign} hours from the pool to {user.username}.')
    else:
        flash('There was an error with the form.')

    return redirect(url_for('index'))


@app.route('/assign', methods=['POST'])
@login_required
def assign_school():
    if current_user.role == 'admin': # Or a new 'coordinator' role
        form = AssignmentForm()
        if form.validate_on_submit():
            user_id = form.user.data
            school_id = form.school.data

            user = User.query.get(user_id)
            school = School.query.get(school_id)

            # Check if school is already fully assigned
            assigned_hours_for_school = db.session.query(func.sum(Assignment.assigned_hours)).filter_by(school_id=school.id).scalar() or 0
            if assigned_hours_for_school >= school.required_hours:
                flash(f'School {school.name} is already fully assigned.')
                return redirect(url_for('index'))

            # Check supervisor's current hours
            current_hours = db.session.query(func.sum(Assignment.assigned_hours)).filter_by(user_id=user.id).scalar() or 0

            if current_hours >= 30:
                flash(f'Supervisor {user.username} already has 30 or more hours.')
                return redirect(url_for('index'))

            # Assign full school hours
            assignment = Assignment(user_id=user.id, school_id=school.id, assigned_hours=school.required_hours)
            db.session.add(assignment)

            # Handle unused hours
            total_assigned = current_hours + school.required_hours
            if total_assigned > 32: # 30 + 2 tolerance
                 flash(f'Assignment exceeds the 32-hour limit for {user.username}.')
                 db.session.rollback()
                 return redirect(url_for('index'))

            if total_assigned > 30:
                unused = total_assigned - 30
                unused_hour_entry = UnusedHour(school_id=school.id, hours=unused)
                db.session.add(unused_hour_entry)

            db.session.commit()
            flash(f'Assigned {school.name} to {user.username}.')

            # Suggest next schools
            remaining_hours_needed = 30 - (total_assigned)
            if 0 < remaining_hours_needed <= 32 - total_assigned:
                 # Suggest schools that fit within the remaining hours + tolerance
                suggestions = School.query.filter(
                    School.required_hours <= remaining_hours_needed + 2,
                    ~School.id.in_([a.school_id for a in user.assignments]) # Exclude already assigned
                ).all()
                if suggestions:
                    flash(f"Suggestions for {user.username}: " + ", ".join([s.name for s in suggestions]))

        else:
            flash('There was an error with the form submission.')
        return redirect(url_for('index'))
    else:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('index'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))

    user_form = UserForm()
    if user_form.validate_on_submit() and 'create_user' in request.form:
        user = User(username=user_form.username.data, role=user_form.role.data)
        user.set_password(user_form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!')
        return redirect(url_for('admin_dashboard'))

    school_form = SchoolForm()
    if school_form.validate_on_submit() and 'add_school' in request.form:
        school = School(name=school_form.name.data, required_hours=school_form.required_hours.data)
        db.session.add(school)
        db.session.commit()
        flash('School added successfully!')
        return redirect(url_for('admin_dashboard'))

    users = User.query.all()
    schools = School.query.all()
    return render_template('admin.html', title='Admin Dashboard', user_form=user_form, school_form=school_form, users=users, schools=schools)

@app.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action.')
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Cannot delete the admin user.')
        return redirect(url_for('admin_dashboard'))

    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_school/<int:school_id>')
@login_required
def delete_school(school_id):
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action.')
        return redirect(url_for('index'))

    school = School.query.get_or_404(school_id)
    db.session.delete(school)
    db.session.commit()
    flash('School deleted successfully.')
    return redirect(url_for('admin_dashboard'))