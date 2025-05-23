from app import app
from models import db, User, Plan, Membership, Staff
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random  # Added for random start dates

def add_sample_data():
    with app.app_context():
        # First, delete any existing data
        Membership.query.delete()
        User.query.delete()  # Remove filter since we no longer have admin users
        Staff.query.delete()
        Plan.query.delete()
        db.session.commit()

        # Create sample plans
        plans = [
            {
                'name': 'Basic Monthly',
                'duration': 1,
                'price': 1000.00,
                'description': 'Access to basic gym facilities'
            },
            {
                'name': 'Premium Quarterly',
                'duration': 3,
                'price': 2700.00,
                'description': 'Access to all facilities including cardio area'
            },
            {
                'name': 'Gold Annual',
                'duration': 12,
                'price': 9999.00,
                'description': 'Full access to all facilities with one free personal training session per month'
            },
            {
                'name': 'Student Special',
                'duration': 6,
                'price': 4500.00,
                'description': 'Special plan for students with valid ID'
            }
        ]

        # Add plans
        db_plans = []
        for plan_data in plans:
            plan_data['duration'] = max(1, plan_data['duration'])
            plan = Plan(**plan_data)
            db.session.add(plan)
            db_plans.append(plan)
        
        # Create sample staff
        staff_members = [
            {
                'name': 'John Smith',
                'email': 'john.trainer@gym.com',
                'phone': '9876543210',
                'position': 'Trainer',
                'salary': 35000.00,
                'address': '123 Fitness Street, City',
                'is_active': True
            },
            {
                'name': 'Sarah Johnson',
                'email': 'sarah.trainer@gym.com',
                'phone': '9876543211',
                'position': 'Trainer',
                'salary': 32000.00,
                'address': '456 Health Avenue, City',
                'is_active': True
            },
            {
                'name': 'Mike Wilson',
                'email': 'mike.trainer@gym.com',
                'phone': '9876543212',
                'position': 'Senior Trainer',
                'salary': 45000.00,
                'address': '789 Muscle Avenue, City',
                'is_active': True
            }
        ]

        # Add staff
        db_staff = []
        for staff_data in staff_members:
            staff = Staff(**staff_data)
            db.session.add(staff)
            db_staff.append(staff)
        
        try:
            # Commit to get IDs
            db.session.commit()

            # Create sample members
            members = [
                {
                    'username': 'rajesh_kumar',
                    'email': 'rajesh@example.com',
                    'phone': '9876543001',
                    'address': '789 Member Lane, City',
                    'trainer_id': db_staff[0].id if db_staff else None,
                    'plan_id': db_plans[2].id if len(db_plans) > 2 else db_plans[0].id
                },
                {
                    'username': 'priya_sharma',
                    'email': 'priya@example.com',
                    'phone': '9876543002',
                    'address': '101 Fitness Road, City',
                    'trainer_id': db_staff[1].id if len(db_staff) > 1 else None,
                    'plan_id': db_plans[1].id if len(db_plans) > 1 else db_plans[0].id
                },
                {
                    'username': 'amit_patel',
                    'email': 'amit@example.com',
                    'phone': '9876543003',
                    'address': '202 Gym Street, City',
                    'trainer_id': db_staff[2].id if len(db_staff) > 2 else None,
                    'plan_id': db_plans[0].id
                },
                {
                    'username': 'neha_gupta',
                    'email': 'neha@example.com',
                    'phone': '9876543004',
                    'address': '303 Health Park, City',
                    'trainer_id': db_staff[0].id if db_staff else None,
                    'plan_id': db_plans[3].id if len(db_plans) > 3 else db_plans[0].id
                },
                {
                    'username': 'rahul_singh',
                    'email': 'rahul@example.com',
                    'phone': '9876543005',
                    'address': '404 Fitness Circle, City',
                    'trainer_id': db_staff[1].id if len(db_staff) > 1 else None,
                    'plan_id': db_plans[1].id if len(db_plans) > 1 else db_plans[0].id
                },
                {
                    'username': 'anita_desai',
                    'email': 'anita@example.com',
                    'phone': '9876543006',
                    'address': '505 Wellness Street, City',
                    'trainer_id': db_staff[2].id if len(db_staff) > 2 else None,
                    'plan_id': db_plans[2].id if len(db_plans) > 2 else db_plans[0].id
                }
            ]

            # Add members and their memberships
            for i, member_data in enumerate(members):
                plan_id = member_data.pop('plan_id')
                trainer_id = member_data.pop('trainer_id')
                
                # Create member with sequential ID
                member = User(
                    password=generate_password_hash('member123'),
                    member_id=str(100001 + i).zfill(6),  # Generate sequential IDs starting from 100001
                    trainer_id=trainer_id,
                    **member_data
                )
                db.session.add(member)
                db.session.flush()  # Get member ID

                # Create membership
                start_date = datetime.utcnow()
                plan = next(p for p in db_plans if p.id == plan_id)
                
                # Add variety to membership start dates
                start_date = start_date - timedelta(days=random.randint(0, 60))
                end_date = start_date + timedelta(days=plan.duration * 30)
                
                membership = Membership(
                    user_id=member.id,
                    plan_id=plan_id,
                    start_date=start_date,
                    end_date=end_date,
                    active=True
                )
                db.session.add(membership)

            # Commit all changes
            db.session.commit()
            
            # Print summary
            print("\n=== Sample Data Added Successfully ===\n")
            
            print("Staff Members:")
            for staff in db_staff:
                print(f"- {staff.name} ({staff.position})")
                print(f"  Email: {staff.email}")
                print(f"  Phone: {staff.phone}\n")
            
            print("Plans:")
            for plan in db_plans:
                print(f"- {plan.name}")
                print(f"  Duration: {plan.duration} months")
                print(f"  Price: ₹{plan.price:.2f}")
                print(f"  Description: {plan.description}\n")
            
            print("Members:")
            members = User.query.all()
            for member in members:
                print(f"- {member.username}")
                print(f"  Member ID: {member.member_id}")
                print(f"  Email: {member.email}")
                print(f"  Phone: {member.phone}")
                if member.membership:
                    print(f"  Start Date: {membership.start_date.strftime('%Y-%m-%d')}")
                    print(f"  End Date: {membership.end_date.strftime('%Y-%m-%d')}")
                print()
                
        except Exception as e:
            db.session.rollback()
            print(f"Error adding sample data: {str(e)}")
            raise  # Re-raise the exception for debugging

if __name__ == '__main__':
    add_sample_data() 