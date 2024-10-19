<<<<<<< HEAD
"""
The Flask application package.
"""
=======
>>>>>>> origin/main
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
<<<<<<< HEAD
app.logger.setLevel(logging.WARNING)

# Create a file handler for logging
log_file = os.path.join(Config.LOG_DIRECTORY, 'app.log')  # Ensure LOG_DIRECTORY is defined in your Config
fileHandler = logging.FileHandler(log_file)
fileHandler.setLevel(logging.WARNING)

# Create a formatter and set it for both handlers
=======
app.logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logging

log_file = os.path.join(Config.LOG_DIRECTORY, 'app.log')  # Ensure LOG_DIRECTORY is defined in your Config
fileHandler = logging.FileHandler(log_file)
fileHandler.setLevel(logging.DEBUG)  # Changed to DEBUG for detailed logs
>>>>>>> origin/main
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

<<<<<<< HEAD
# Add handlers to the app logger
=======
>>>>>>> origin/main
app.logger.addHandler(streamHandler)
app.logger.addHandler(fileHandler)

# Initialize extensions
Session(app)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

# Import views
import FlaskWebProject.views

# Ensure the app runs on port 8000
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
