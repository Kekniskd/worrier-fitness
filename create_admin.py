from app import app
from models import db, User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("Admin user already exists!")

if __name__ == '__main__':
    create_admin() 