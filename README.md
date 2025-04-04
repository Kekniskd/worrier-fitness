# Gym Management System

A Flask-based web application for managing gym memberships, tracking attendance, and monitoring client progress.

## Features

- User Authentication (Admin/Client)
- Membership Plan Management
- Attendance Tracking
- Member Progress Monitoring
- Plan Expiry Tracking
- Responsive Dashboard

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd gym-management-system
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. The application uses SQLite as the database by default. The database file will be created automatically when you run the application.

2. To create an admin user, you can use the Python shell:
```bash
python
>>> from app import app, db, User
>>> from werkzeug.security import generate_password_hash
>>> with app.app_context():
...     admin = User(username='admin', email='admin@example.com', password=generate_password_hash('your-password'), is_admin=True)
...     db.session.add(admin)
...     db.session.commit()
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Admin Users Can:**
   - Manage membership plans
   - View all members
   - Track member attendance
   - Monitor membership status

2. **Regular Users Can:**
   - View available plans
   - Enroll in plans
   - Mark daily attendance
   - View their attendance history
   - Check membership status

## Security

- Passwords are hashed using Werkzeug's security features
- User sessions are managed securely
- Form CSRF protection is enabled
- Input validation is implemented

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
