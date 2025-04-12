from app import app
from models import db, Moderator
from werkzeug.security import generate_password_hash

def create_moderators():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create admin moderator if not exists
        admin = Moderator.query.filter_by(username='admin').first()
        if not admin:
            admin = Moderator(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            
        # Create regular moderator if not exists
        moderator = Moderator.query.filter_by(username='moderator').first()
        if not moderator:
            moderator = Moderator(
                username='moderator',
                email='moderator@example.com',
                password=generate_password_hash('moderator123'),
                role='moderator'
            )
            db.session.add(moderator)
        
        try:
            db.session.commit()
            print("Moderator accounts created successfully!")
            print("\nAdmin account:")
            print("Username: admin")
            print("Password: admin123")
            print("\nModerator account:")
            print("Username: moderator")
            print("Password: moderator123")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating moderator accounts: {str(e)}")

if __name__ == '__main__':
    create_moderators() 