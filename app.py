from flask import Flask
from flask_login import LoginManager
import os
from models import db, Moderator


def create_app():
    # flaskapp = Flask(__name__)
    # app = ASGIApp(flaskapp)

    app = Flask(__name__)
    # app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gym.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # logging.basicConfig(level=logging.DEBUG)
    # app.logger.setLevel(logging.DEBUG)

    
    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return Moderator.query.get(int(user_id))

    # Create database tables only if they don't exist
    with app.app_context():
        db.create_all()

    return app, db

app, db = create_app()

# Import routes after app is created
from routes import *

if __name__ == '__main__':
    app.run(debug=True, port=5000)