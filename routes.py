from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import random
import string
import pywhatkit
import time
from app import app
from models import db, User, Plan, Membership, Attendance, Staff, StaffAttendance, StaffPayment, Moderator
from sqlalchemy import inspect


def object_as_dict(obj):
    members_list = []
    for mem in obj:
        data = {
        c.key: getattr(mem, c.key)
        for c in inspect(mem).mapper.column_attrs
    }
        members_list.append(data)
    return members_list

def generate_member_id():
    """Generate a unique 6-digit member ID"""
    while True:
        member_id = ''.join(random.choices(string.digits, k=6))
        if not User.query.filter_by(member_id=member_id).first():
            return member_id

def format_phone_number(phone):
    """Format phone number for WhatsApp by removing any non-digit characters and adding country code."""
    # Remove any non-digit characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # Add country code if not present (assuming Indian numbers)
    if len(phone) == 10:
        phone = '+91' + phone
    elif not phone.startswith('+'):
        phone = '+' + phone
        
    return phone

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        moderator = Moderator.query.filter_by(username=username).first()
        
        if moderator and check_password_hash(moderator.password, password):
            login_user(moderator)
            moderator.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user, Moderator):
        logout_user()
        return redirect(url_for('login'))
    
    total_members = User.query.count()
    active_plans = Plan.query.count()
    today = datetime.utcnow()
    today_attendance = Attendance.query.filter(
        db.func.date(Attendance.date) == today.date()
    ).count()
    
    # Get members with expiring memberships (within next 7 days)
    expiring_date = today + timedelta(days=7)
    expiring_memberships = (
        Membership.query
        .join(User)
        .filter(
            Membership.end_date > today,
            Membership.end_date <= expiring_date,
            Membership.active == True
        )
        .order_by(Membership.end_date)
        .all()
    )
    
    recent_members = User.query.order_by(User.id.desc()).limit(5).all()
    
    # Count members with expiring memberships for each reminder day
    expiry_counts = {
        'one_day': Membership.query.join(User).filter(
            db.func.date(Membership.end_date) == (today + timedelta(days=1)).date(),
            Membership.active == True
        ).count(),
        'three_days': Membership.query.join(User).filter(
            db.func.date(Membership.end_date) == (today + timedelta(days=3)).date(),
            Membership.active == True
        ).count(),
        'seven_days': Membership.query.join(User).filter(
            db.func.date(Membership.end_date) == (today + timedelta(days=7)).date(),
            Membership.active == True
        ).count()
    }
    
    return render_template('admin_dashboard.html', 
                         total_members=total_members,
                         active_plans=active_plans,
                         today_attendance=today_attendance,
                         recent_members=recent_members,
                         expiring_memberships=expiring_memberships,
                         expiry_counts=expiry_counts,
                         today=today)

def check_moderator_access():
    if not isinstance(current_user, Moderator):
        return False
    if current_user.role == 'admin':
        return True
    return True  # For now allowing all moderators, you can add more specific checks

@app.route('/mark-attendance', methods=['GET', 'POST'])
def public_attendance():
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        if not member_id:
            flash('Please enter your Member ID', 'error')
            return redirect(url_for('public_attendance'))
        
        member = User.query.filter_by(member_id=member_id).first()
        if not member:
            flash('Invalid Member ID', 'error')
            return redirect(url_for('public_attendance'))
        
        # Check if member has active membership
        current_membership = next((m for m in member.membership if m.active), None)
        if not current_membership:
            flash('Your membership is not active. Please contact the admin.', 'error')
            return redirect(url_for('public_attendance'))
        
        # Check if attendance already marked today
        today = datetime.utcnow().date()
        existing_attendance = Attendance.query.filter(
            Attendance.user_id == member.id,
            db.func.date(Attendance.date) == today
        ).first()
        
        if existing_attendance:
            flash(f'Attendance already marked for today', 'info')
        else:
            attendance = Attendance(user_id=member.id)
            db.session.add(attendance)
            try:
                db.session.commit()
                flash('Attendance marked successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error marking attendance', 'error')
                print(f"Error marking attendance: {str(e)}")
        
        return redirect(url_for('public_attendance'))
    
    return render_template('public_attendance.html')

@app.route('/add-member', methods=['GET', 'POST'])
@login_required
def add_member():
    if not check_moderator_access():
        return redirect(url_for('login'))
    
    plans = Plan.query.all()
    trainers = Staff.query.filter_by(position='Trainer', is_active=True).all()
    selected_plan_id = request.args.get('plan_id', type=int)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        plan_id = request.form.get('plan_id')
        trainer_id = request.form.get('trainer_id')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('add_member'))
        
        # Create new member with a unique member ID
        password = 'member123'  # Default password
        new_member = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            phone=phone,
            address=address,
            trainer_id=trainer_id if trainer_id else None,
            member_id=generate_member_id()  # Generate unique member ID
        )
        db.session.add(new_member)
        db.session.flush()  # Get the new member's ID
        
        # Create membership if plan selected
        if plan_id:
            plan = Plan.query.get(plan_id)
            if plan:
                start_date = datetime.utcnow()
                end_date = start_date + timedelta(days=plan.duration * 30)
                
                membership = Membership(
                    user_id=new_member.id,
                    plan_id=plan_id,
                    start_date=start_date,
                    end_date=end_date,
                    active=True
                )
                db.session.add(membership)
        
        try:
            db.session.commit()
            flash(f'Member added successfully. Member ID: {new_member.member_id}')
            return redirect(url_for('view_members'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding member')
            print(f"Error adding member: {str(e)}")
            
    return render_template('members/add_member.html', 
                         plans=plans, 
                         trainers=trainers,
                         selected_plan_id=selected_plan_id)

@app.route('/plans')
@login_required
def plans():
    if not check_moderator_access():
        return redirect(url_for('login'))
    
    all_plans = Plan.query.all()
    return render_template('members/plans.html', all_plans=all_plans)

@app.route('/add-plan', methods=['GET', 'POST'])
@login_required
def add_plan():
    if not check_moderator_access():
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        duration = int(request.form.get('duration'))
        price = float(request.form.get('price'))
        description = request.form.get('description')
        
        new_plan = Plan(name=name, duration=duration, price=price, description=description)
        db.session.add(new_plan)
        db.session.commit()
        
        flash('Plan added successfully')
        return redirect(url_for('plans'))
    
    return render_template('members/add_plan.html')

@app.route('/delete-plan/<int:plan_id>', methods=['POST'])
@login_required
def delete_plan(plan_id):
    if not check_moderator_access():
        return redirect(url_for('login'))
    
    plan = Plan.query.get_or_404(plan_id)
    
    # Check if there are any active memberships for this plan
    active_memberships = Membership.query.filter_by(plan_id=plan_id, active=True).first()
    if active_memberships:
        flash('Cannot delete plan: There are active memberships using this plan')
        return redirect(url_for('plans'))
    
    try:
        # Delete associated memberships first
        Membership.query.filter_by(plan_id=plan_id).delete()
        # Delete the plan
        db.session.delete(plan)
        db.session.commit()
        flash('Plan deleted successfully')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting plan')
        print(f"Error deleting plan: {str(e)}")
    
    return redirect(url_for('plans'))

@app.route('/view-members')
@login_required
def view_members():
    if not check_moderator_access():
        return redirect(url_for('login'))
    
    members = User.query.all()
    today = datetime.utcnow().date()
    
    attendance_data = {
        attendance.user_id: attendance 
        for attendance in Attendance.query.filter(
            db.func.date(Attendance.date) == today
        ).all()
    }
    
    return render_template('members/list.html', 
                         members=members,
                         attendance_data=attendance_data,
                         today=today)

@app.route('/member/<int:user_id>')
@login_required
def member_details(user_id):
    if not check_moderator_access():
        return redirect(url_for('login'))
    
    member = User.query.get_or_404(user_id)
    today = datetime.utcnow().date()
    return render_template('members/details.html', member=member, today=today)

@app.route('/delete-member/<int:user_id>', methods=['POST'])
@login_required
def delete_member(user_id):
    if not check_moderator_access():
        return redirect(url_for('login'))
    
    member = User.query.get_or_404(user_id)
    
    try:
        # Delete associated records
        Attendance.query.filter_by(user_id=user_id).delete()
        Membership.query.filter_by(user_id=user_id).delete()
        db.session.delete(member)
        db.session.commit()
        flash('Member deleted successfully')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting member')
        print(f"Error deleting member: {str(e)}")
    
    return redirect(url_for('view_members'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def check_admin_access():
    """Check if the current user is an admin moderator"""
    if not isinstance(current_user, Moderator):
        return False
    return current_user.role == 'admin'

@app.route('/staff')
@login_required
def view_staff():
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    staff_members = Staff.query.all()
    today = datetime.utcnow()
    
    # Get today's attendance for each staff member
    attendance_data = {
        attendance.staff_id: attendance 
        for attendance in StaffAttendance.query.filter(
            db.func.date(StaffAttendance.date) == today.date()
        ).all()
    }
    
    return render_template('staff/staff_list.html', 
                         staff_members=staff_members,
                         attendance_data=attendance_data,
                         today=today)

@app.route('/staff/add', methods=['GET', 'POST'])
@login_required
def add_staff():
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        position = request.form.get('position')
        salary = float(request.form.get('salary'))
        address = request.form.get('address')
        
        if Staff.query.filter_by(email=email).first():
            flash('Email already exists', 'warning')
            return redirect(url_for('add_staff'))
        
        new_staff = Staff(
            name=name,
            email=email,
            phone=phone,
            position=position,
            salary=salary,
            address=address
        )
        
        try:
            db.session.add(new_staff)
            db.session.commit()
            flash('Staff member added successfully', 'success')
            return redirect(url_for('view_staff'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding staff member', 'danger')
            print(f"Error adding staff: {str(e)}")
    
    return render_template('staff/add_staff.html')

@app.route('/staff/<int:staff_id>')
@login_required
def staff_details(staff_id):
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    staff = Staff.query.get_or_404(staff_id)
    attendance_history = StaffAttendance.query.filter_by(staff_id=staff_id).order_by(StaffAttendance.date.desc()).limit(30).all()
    payment_history = StaffPayment.query.filter_by(staff_id=staff_id).order_by(StaffPayment.payment_date.desc()).all()
    
    return render_template('staff/staff_details.html',
                         staff=staff,
                         attendance_history=attendance_history,
                         payment_history=payment_history)

@app.route('/staff/attendance', methods=['GET', 'POST'])
@login_required
def staff_attendance():
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    staff_members = Staff.query.filter_by(is_active=True).all()
    today = datetime.utcnow().date()
    
    if request.method == 'POST':
        staff_id = request.form.get('staff_id')
        status = request.form.get('status')
        
        if not staff_id or not status:
            flash('Invalid attendance data provided.', 'danger')
            return redirect(url_for('staff_attendance'))
        
        # Validate status
        if status not in ['present', 'late', 'absent']:
            flash('Invalid attendance status.', 'danger')
            return redirect(url_for('staff_attendance'))
        
        # Check if staff exists and is active
        staff = Staff.query.filter_by(id=staff_id, is_active=True).first()
        if not staff:
            flash('Invalid staff member.', 'danger')
            return redirect(url_for('staff_attendance'))
        
        # Check for existing attendance
        existing_attendance = StaffAttendance.query.filter(
            StaffAttendance.staff_id == staff_id,
            db.func.date(StaffAttendance.date) == today
        ).first()
        
        if existing_attendance:
            flash('Attendance already marked for this staff member today.', 'warning')
        else:
            # Create new attendance record
            attendance = StaffAttendance(
                staff_id=staff_id,
                status=status,
                check_in=datetime.utcnow(),
                date=datetime.utcnow()
            )
            
            try:
                db.session.add(attendance)
                db.session.commit()
                flash(f'Attendance marked as {status} for {staff.name}.', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error marking attendance.', 'danger')
                print(f"Error marking attendance: {str(e)}")
    
    # Get today's attendance for display
    attendance_data = {
        att.staff_id: att for att in StaffAttendance.query.filter(
            db.func.date(StaffAttendance.date) == today
        ).all()
    }
    
    staff_members_deactive = Staff.query.filter_by(is_active=False).all()


    # Calculate attendance statistics
    total_staff = len(staff_members)
    marked_attendance = len(attendance_data)
    present_count = sum(1 for att in attendance_data.values() if att.status == 'present')
    late_count = sum(1 for att in attendance_data.values() if att.status == 'late')
    absent_count = sum(1 for att in attendance_data.values() if att.status == 'absent')
    deactivated_count = sum(1 for staff in staff_members_deactive)
    not_marked = total_staff - marked_attendance + deactivated_count
    
    return render_template('staff/attendance.html',
                         staff_members=staff_members,
                         attendance_data=attendance_data,
                         today=datetime.utcnow(),
                         stats={
                             'total': total_staff,
                             'present': present_count,
                             'late': late_count,
                             'absent': absent_count,
                             'not_marked': not_marked
                         })

@app.route('/staff/payments', methods=['GET'])
@login_required
def staff_payments():
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    staff_members = Staff.query.filter_by(is_active=True).all()
    current_month = datetime.utcnow().replace(day=1).date()
    
    # Get this month's payments using SQLite's strftime function
    payments = StaffPayment.query.filter(
        db.func.strftime('%Y-%m', StaffPayment.payment_for_month) == current_month.strftime('%Y-%m')
    ).all()
    
    payment_data = {payment.staff_id: payment for payment in payments}
    
    return render_template('staff/payments.html',
                         staff_members=staff_members,
                         payment_data=payment_data,
                         current_month=current_month)

@app.route('/staff/payment/<int:staff_id>', methods=['GET', 'POST'])
@login_required
def record_staff_payment(staff_id):
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    staff = Staff.query.get_or_404(staff_id)
    
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        payment_for_month = datetime.strptime(request.form.get('payment_for_month'), '%Y-%m').date()
        payment_method = request.form.get('payment_method')
        status = request.form.get('status')
        notes = request.form.get('notes')
        
        # Check if payment already exists for this month using SQLite's strftime
        existing_payment = StaffPayment.query.filter(
            StaffPayment.staff_id == staff_id,
            db.func.strftime('%Y-%m', StaffPayment.payment_for_month) == payment_for_month.strftime('%Y-%m')
        ).first()
        
        if existing_payment:
            flash(f'Payment already recorded for {payment_for_month.strftime("%B %Y")}', 'warning')
            return redirect(url_for('staff_payments'))
        
        payment = StaffPayment(
            staff_id=staff_id,
            amount=amount,
            payment_for_month=payment_for_month,
            payment_method=payment_method,
            status=status,
            notes=notes
        )
        
        try:
            db.session.add(payment)
            db.session.commit()
            flash('Payment recorded successfully', 'success')
            return redirect(url_for('staff_payments'))
        except Exception as e:
            db.session.rollback()
            flash('Error recording payment', 'danger')
            print(f"Error recording payment: {str(e)}")
    
    return render_template('staff/record_payment.html', staff=staff)

@app.route('/staff/deactivate/<int:staff_id>', methods=['POST'])
@login_required
def deactivate_staff(staff_id):
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    staff = Staff.query.get_or_404(staff_id)
    if not staff.is_active:
        flash('Staff member is already inactive.', 'info')
        return redirect(url_for('view_staff'))
    
    try:
        staff.is_active = False
        db.session.commit()
        flash(f'Staff member {staff.name} has been deactivated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deactivating staff member.', 'danger')
        print(f"Error deactivating staff: {str(e)}")
    
    return redirect(url_for('view_staff'))

@app.route('/announcements', methods=['GET', 'POST'])
@login_required
def announcements():
    if not check_moderator_access():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        message = request.form.get('message')
        recipient_type = request.form.get('recipient_type', 'all')  # Changed from send_to to recipient_type
        
        if not message:
            flash('Please enter a message', 'error')
            return redirect(url_for('announcements'))
        
        # Get members based on selection
        if recipient_type == 'active':  # Updated variable name
            members = User.query\
                .join(Membership)\
                .filter(Membership.active == True).all()
        elif recipient_type == 'expired':  # Updated variable name
            members = User.query\
                .join(Membership)\
                .filter(Membership.active == False).all()
        else:  # 'all'
            members = User.query.all()
        
        success_count = 0
        failed_numbers = []
        test = object_as_dict(members)
        print(test)
        for member in members:
            if member.phone:
                try:
                    phone = format_phone_number(member.phone)
                    # Ensure message is properly formatted
                    formatted_message = f"Gym Announcement\n\n{message}\n\nBest regards,\nGym Management"
                    
                    # Add a small delay before sending
                    time.sleep(2)
                    
                    # Send message with minimal wait time and close tab
                    pywhatkit.sendwhatmsg_instantly(
                        phone_no=phone,
                        message=formatted_message,
                        wait_time=15,  # Increased wait time to ensure browser loads
                        tab_close=True,
                        close_time=3   # Wait 3 seconds before closing tab
                    )
                    
                    success_count += 1
                    # Add delay after sending
                    time.sleep(3)
                    
                except Exception as e:
                    failed_numbers.append(member.phone)
                    print(f"Error sending message to {member.phone}: {str(e)}")
                    # Add delay even on failure to prevent rate limiting
                    time.sleep(2)
        
        if success_count > 0:
            flash(f'Successfully sent announcement to {success_count} members', 'success')
        if failed_numbers:
            flash(f'Failed to send to {len(failed_numbers)} numbers: {", ".join(failed_numbers)}', 'warning')
        
        return redirect(url_for('announcements'))
    
    # Get counts for different member categories
    total_members = User.query.count()
    active_members = User.query\
        .join(Membership)\
        .filter(Membership.active == True).count()
    expired_members = total_members - active_members
    
    return render_template('announcements.html',
                         total_members=total_members,
                         active_members=active_members,
                         expired_members=expired_members)

@app.route('/send-expiry-reminders')
@login_required
def send_expiry_reminders():
    if not check_moderator_access():
        return redirect(url_for('login'))
    
    today = datetime.utcnow()
    success_count = 0
    failed_numbers = []
    
    # Check for memberships expiring in 7 days, 3 days, and 1 day
    reminder_days = [7, 3, 1]
    
    for days in reminder_days:
        target_date = today + timedelta(days=days)
        
        # Find memberships expiring on target date
        expiring_memberships = (
            Membership.query
            .join(User)
            .filter(
                db.func.date(Membership.end_date) == target_date.date(),
                Membership.active == True)
            .all()
        )
        
        for membership in expiring_memberships:
            member = membership.user
            if member.phone:
                try:
                    phone = format_phone_number(member.phone)
                    
                    # Prepare reminder message
                    if days == 1:
                        message = (
                            f"⚠️ URGENT: Membership Expiry Tomorrow ⚠️\n\n"
                            f"Dear {member.username},\n"
                            f"Your gym membership will expire TOMORROW. "
                            f"Please renew your membership to continue enjoying our facilities.\n\n"
                            f"Current Plan: {membership.plan.name}\n"
                            f"Expiry Date: {membership.end_date.strftime('%d-%m-%Y')}\n\n"
                            f"Visit us today to renew your membership!\n\n"
                            f"Best regards,\nGym Management"
                        )
                    elif days == 3:
                        message = (
                            f"🔔 Membership Expiry Reminder 🔔\n\n"
                            f"Dear {member.username},\n"
                            f"Your gym membership will expire in 3 days. "
                            f"Don't forget to renew your membership to avoid any interruption.\n\n"
                            f"Current Plan: {membership.plan.name}\n"
                            f"Expiry Date: {membership.end_date.strftime('%d-%m-%Y')}\n\n"
                            f"Visit us soon to renew your membership!\n\n"
                            f"Best regards,\nGym Management"
                        )
                    else:  # 7 days
                        message = (
                            f"📅 Membership Expiry Notice 📅\n\n"
                            f"Dear {member.username},\n"
                            f"This is a friendly reminder that your gym membership "
                            f"will expire in 7 days.\n\n"
                            f"Current Plan: {membership.plan.name}\n"
                            f"Expiry Date: {membership.end_date.strftime('%d-%m-%Y')}\n\n"
                            f"Please plan your renewal accordingly.\n\n"
                            f"Best regards,\nGym Management"
                        )
                    
                    # Add delay before sending
                    time.sleep(2)
                    
                    # Send WhatsApp message
                    pywhatkit.sendwhatmsg_instantly(
                        phone_no=phone,
                        message=message,
                        wait_time=15,
                        tab_close=True,
                        close_time=3
                    )
                    
                    success_count += 1
                    # Add delay after sending
                    time.sleep(3)
                    
                except Exception as e:
                    failed_numbers.append(member.phone)
                    print(f"Error sending reminder to {member.phone}: {str(e)}")
                    # Add delay even on failure
                    time.sleep(2)
    
    if success_count > 0:
        flash(f'Successfully sent reminders to {success_count} members', 'success')
    if failed_numbers:
        flash(f'Failed to send to {len(failed_numbers)} numbers: {", ".join(failed_numbers)}', 'warning')
    
    return redirect(url_for('dashboard'))

@app.route('/staff/reactivate/<int:staff_id>', methods=['POST'])
@login_required
def reactivate_staff(staff_id):
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    staff = Staff.query.get_or_404(staff_id)
    if staff.is_active:
        flash('Staff member is already active.', 'info')
        return redirect(url_for('view_staff'))
    
    try:
        staff.is_active = True
        db.session.commit()
        flash(f'Staff member {staff.name} has been reactivated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error reactivating staff member.', 'danger')
        print(f"Error reactivating staff: {str(e)}")
    
    return redirect(url_for('view_staff'))

@app.route('/member/renew/<int:member_id>', methods=['GET', 'POST'])
@login_required
def renew_membership(member_id):
    if not check_moderator_access():
        return redirect(url_for('login'))
    
    member = User.query.get_or_404(member_id)
    today = datetime.utcnow().date()
    
    if request.method == 'POST':
        plan_id = request.form.get('plan_id')
        payment_method = request.form.get('payment_method')
        
        # Validate required fields
        if not plan_id:
            flash('Please select a membership plan.', 'danger')
            return redirect(url_for('renew_membership', member_id=member_id))
        
        if not payment_method:
            flash('Please select a payment method.', 'danger')
            return redirect(url_for('renew_membership', member_id=member_id))
        
        plan = Plan.query.get_or_404(plan_id)
        amount = plan.price  # Get amount directly from the plan
        
        try:
            # Get the most recent active membership if any
            current_membership = Membership.query.filter_by(
                user_id=member_id,
                active=True
            ).order_by(Membership.end_date.desc()).first()

            # Calculate new expiry date
            if current_membership and current_membership.end_date > datetime.utcnow():
                # If current membership hasn't expired, extend from current expiry
                new_expiry = current_membership.end_date + timedelta(days=30 * plan.duration)
            else:
                # If expired or no active membership, start from today
                new_expiry = datetime.utcnow().date() + timedelta(days=30 * plan.duration)
            
            # Deactivate current membership if exists
            if current_membership:
                current_membership.active = False
            
            # Create new membership
            new_membership = Membership(
                user_id=member_id,
                plan_id=plan_id,
                start_date=datetime.utcnow(),
                end_date=new_expiry,
                active=True
            )
            
            db.session.add(new_membership)
            db.session.commit()
            
            flash(f'Membership renewed successfully. New expiry date: {new_expiry.strftime("%Y-%m-%d")}', 'success')
            return redirect(url_for('member_details', user_id=member_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error renewing membership.', 'danger')
            print(f"Error renewing membership: {str(e)}")
    
    plans = Plan.query.all()
    return render_template('members/renew.html', member=member, plans=plans, today=today) 