"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, flash, redirect, request, session, url_for
from werkzeug.urls import url_parse
from config import Config
from FlaskWebProject import app, db
from FlaskWebProject.forms import LoginForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from FlaskWebProject.models import User, Post
import msal
import uuid
from typing import Optional, List, Any

imageSourceUrl = 'https://'+ app.config['BLOB_ACCOUNT']  + '.blob.core.windows.net/' + app.config['BLOB_CONTAINER']  + '/'

@app.route('/')
@app.route('/home')
@login_required
def home():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    posts = Post.query.all()
    return render_template(
        'index.html',
        title='Home Page',
        posts=posts
    )

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm(request.form)
    if form.validate_on_submit():
        post = Post()
        post.save_changes(form, request.files['image_path'], current_user.id, new=True)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Create Post',
        imageSource=imageSourceUrl,
        form=form
    )


@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    post = Post.query.get(int(id))
    form = PostForm(formdata=request.form, obj=post)
    if form.validate_on_submit():
        post.save_changes(form, request.files['image_path'], current_user.id)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Edit Post',
        imageSource=imageSourceUrl,
        form=form
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password_hash == '-': 
            # OAuth2 users are not allowed to use password
            flash('Not Allowed! Sign in with your Microsoft Account')
            return redirect(url_for('login'))
        elif user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            # Log for unsuccessful login attempt:
            app.logger.warning("Invalid login attempt!")
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        # Log for successful login:
        app.logger.info(f"{user.username} logged in successfully")
        flash(f'Welcome {user.username} !')
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=Config.SCOPE, state=session["state"])
    return render_template('login.html', title='Sign In', form=form, auth_url=auth_url)

@app.route(Config.REDIRECT_PATH)  
def authorized():
    if request.args.get('state') != session.get("state"):
        return redirect(url_for("home"))  # No-OP. Goes back to Index page
    if "error" in request.args:  # Authentication/Authorization failure
        return render_template("auth_error.html", result=request.args)
    if request.args.get('code'):
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            code=request.args['code'],
            scopes=Config.SCOPE,
            redirect_uri=url_for('authorized', _external=True, _scheme="https"))
        session["user"] = result.get("id_token_claims")
        # Get user name from result, preferred_username is email
        username = session["user"].get('preferred_username').split('@')[0] # Preprocess the email and use it for username
        user = User.query.filter_by(username=username).first()
        if not user:
            new_user = User(username=username,password_hash='-')
            db.session.add(new_user)
            db.session.commit()
            user = User.query.filter_by(username=username).first()
        login_user(user)
        flash(f'Welcome {user.username} !')
        _save_cache(cache)
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    logout_user()
    if session.get("user"): # Used MS Login
        # Wipe out user and its token cache from session
        session.clear()
        # Also logout from your tenant's web session
        return redirect(
            Config.AUTHORITY + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for("login", _external=True))

    return redirect(url_for('login'))


def _load_cache() -> msal.SerializableTokenCache:
    """
    Loads the token cache from the session, if it exists.

    Returns:
        msal.SerializableTokenCache: An instance of SerializableTokenCache containing 
                                      the loaded token cache, or an empty cache if none exists.
    """
    # Create a new instance of SerializableTokenCache
    cache = msal.SerializableTokenCache()
    
    # Retrieve the token cache from the session
    token_cache = session.get('token_cache')
    
    # If a token cache exists in the session, deserialize it
    if token_cache:
        cache.deserialize(token_cache)
    
    return cache




def _save_cache(cache: Any) -> None:
    """
    Saves the token cache to the session if it has changed.

    Parameters:
        cache (Any): The token cache to be saved. It should have a method `has_state_changed`
                     to check if it has changed and a method `serialize` to get the serialized
                     representation of the cache.

    Returns:
        None
    """
    # Check if the cache state has changed and save it to the session
    if cache.has_state_changed:
        session['token_cache'] = cache.serialize()



def _build_msal_app(cache: Optional[msal.TokenCache] = None, authority: Optional[str] = None) -> msal.ConfidentialClientApplication:
    """
    Builds and returns an instance of MSAL's ConfidentialClientApplication.

    Parameters:
        cache (msal.TokenCache, optional): Token cache to store access tokens. Defaults to None.
        authority (str, optional): The authority to authenticate against. If not provided, uses the default from Config.

    Returns:
        msal.ConfidentialClientApplication: An MSAL application instance used for acquiring tokens.
    """
    # Use the provided authority or fallback to the default from the configuration
    authority_url = authority or Config.AUTHORITY

    # Return an instance of ConfidentialClientApplication
    return msal.ConfidentialClientApplication(
        authority=authority_url,
        client_id=Config.CLIENT_ID,
        client_credential=Config.CLIENT_SECRET,
        token_cache=cache
    )



def _build_auth_url(authority: Optional[str] = None, scopes: Optional[List[str]] = None, state: Optional[str] = None) -> str:
    """
    Builds the authorization URL using the MSAL app.

    Parameters:
        authority (str): The authority to authenticate against.
        scopes (list of str): The requested API permissions (scopes).
        state (str): An optional state value to maintain state between request and callback.

    Returns:
        str: The authorization request URL.
    """
    # Generate the state if not provided
    state_value = state or str(uuid.uuid4())

    # Set default scopes if not provided
    scopes_list = scopes or []

    # Build the MSAL app and generate the authorization request URL
    msal_app = _build_msal_app(authority=authority)
    
    auth_url = msal_app.get_authorization_request_url(
        scopes=scopes_list,
        state=state_value,
        redirect_uri=url_for('authorized', _external=True, _scheme='https')
    )
    return auth_url
