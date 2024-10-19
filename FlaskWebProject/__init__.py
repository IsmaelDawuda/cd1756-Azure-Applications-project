"""
The Flask application package.
"""
import logging
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session
import os

app = Flask(__name__)
app.config.from_object(Config)

# Set up logging
app.logger.setLevel(logging.WARNING)

# Create a file handler for logging
log_file = os.path.join(Config.LOG_DIRECTORY, 'app.log')  # Ensure LOG_DIRECTORY is defined in your Config
fileHandler = logging.FileHandler(log_file)
fileHandler.setLevel(logging.WARNING)

# Create a formatter and set it for both handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

# Add handlers to the app logger
app.logger.addHandler(streamHandler)
app.logger.addHandler(fileHandler)

# Initialize extensions
Session(app)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

# Import views
import FlaskWebProject.views
