from os import environ
from FlaskWebProject import app

if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', '0.0.0.0')
    try:
        PORT = int(environ.get('PORT', '8000'))  # Changed to 'PORT'
    except ValueError:
        PORT = 8000
    app.run(HOST, PORT, ssl_context='adhoc')
