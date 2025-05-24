#!/usr/bin/python3

from flask import Flask, render_template, request, redirect, url_for, Blueprint, jsonify, Response
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import re
import secrets
import os
from functools import wraps

class NewsletterApp:
    """
    This class implements a newsletter signup web application with topic preferences.
    """

    def __init__(self) -> None:
        """
        Initialize NewsletterApp.
        """
        # Flask app
        self.app: Flask = Flask(__name__)
        # Create a Blueprint for the newsletter
        self.newsletter_bp = Blueprint('newsletter', __name__, url_prefix='/newsletter')
        # MongoDB setup
        self.client = MongoClient('mongodb://newsletter-db-1:27017/')
        self.db = self.client['newsletter_db']
        self.collection = self.db['subscribers']

        # Available topics
        self.TOPICS = {
            'red_teaming': 'Red Teaming',
            'safety': 'Safety',
            'governance': 'Risk & Governance'
        }

        # Admin credentials from environment variables
        self.ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
        self.ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'changeme')

        # Setup routes
        self.setup_routes()

        # Register the Blueprint
        self.app.register_blueprint(self.newsletter_bp)

        # Create index on email for better performance
        self.collection.create_index('email', unique=True)

    def setup_routes(self) -> None:
        """
        Setup Flask application routes.
        """
        # Route for the homepage
        @self.newsletter_bp.route('/', methods=['GET'])
        def home():
            return self.render_home()

        # Route for checking user preferences
        @self.newsletter_bp.route('/check-preferences', methods=['POST'])
        def check_preferences():
            return self.check_user_preferences()

        # Route for the signup/update form
        @self.newsletter_bp.route('/signup', methods=['POST'])
        def signup():
            return self.handle_signup()

        # Route for the opt-out form
        @self.newsletter_bp.route('/optout', methods=['POST'])
        def optout():
            return self.handle_optout()

        # Route to get all new sign-ups
        @self.newsletter_bp.route('/fb0454df-1b01-48fa-9b1e-58d4d3c282ac-6911e296-dc31-4afc-b9ed-f03bfc7d879b', methods=['GET'])
        @self.requires_auth
        def get_sign_ups():
            return self.handle_get_sign_ups()

        # Route for preferences management page (via secure token)
        @self.newsletter_bp.route('/preferences/<token>', methods=['GET'])
        def preferences(token):
            return self.render_preferences(token)

        # Route for updating preferences via token
        @self.newsletter_bp.route('/preferences/<token>', methods=['POST'])
        def update_preferences(token):
            return self.handle_update_preferences(token)

    def render_home(self, success=None, error=None) -> str:
        """
        Render the homepage template with topics.

        :return: Rendered HTML of the homepage
        """
        return render_template('home.html', 
                             success=success, 
                             error=error,
                             topics=self.TOPICS)

    def check_auth(self, username: str, password: str) -> bool:
        """
        Check if username/password combination is valid.
        
        :param username: Username to check
        :param password: Password to check
        :return: True if valid, False otherwise
        """
        return username == self.ADMIN_USERNAME and password == self.ADMIN_PASSWORD

    def authenticate(self) -> Response:
        """
        Send a 401 response that enables basic auth.
        
        :return: 401 Response with auth headers
        """
        return Response(
            'Authentication required. Please provide valid credentials.',
            401,
            {'WWW-Authenticate': 'Basic realm="Admin Access"'}
        )

    def requires_auth(self, f):
        """
        Decorator to require basic authentication for a route.
        
        :param f: Function to wrap
        :return: Wrapped function
        """
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not self.check_auth(auth.username, auth.password):
                return self.authenticate()
            return f(*args, **kwargs)
        return decorated

    def check_user_preferences(self) -> dict:
        """
        Check if user exists and return their preferences.
        
        :return: JSON response with user preferences or empty if not found
        """
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not self.is_valid_email(email):
            return jsonify({'exists': False})
        
        subscriber = self.collection.find_one({'email': email})
        
        if subscriber:
            return jsonify({
                'exists': True,
                'topics': subscriber.get('topics', []),
                'frequency': subscriber.get('frequency', 'immediate')
            })
        else:
            return jsonify({'exists': False})
        """
        Check if user exists and return their preferences.
        
        :return: JSON response with user preferences or empty if not found
        """
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not self.is_valid_email(email):
            return jsonify({'exists': False})
        
        subscriber = self.collection.find_one({'email': email})
        
        if subscriber:
            return jsonify({
                'exists': True,
                'topics': subscriber.get('topics', []),
                'frequency': subscriber.get('frequency', 'immediate')
            })
        else:
            return jsonify({'exists': False})

    def handle_signup(self) -> str:
        """
        Handle the signup form submission with preferences.

        :return: Redirect to homepage after signup or render an error
        """
        email = request.form.get('email', '').strip()
        topics = request.form.getlist('topics')
        frequency = request.form.get('frequency', 'immediate')

        if not self.is_valid_email(email):
            return self.render_home(error='Invalid email address.')

        if not topics:
            return self.render_home(error='Please select at least one topic.')

        existing_subscriber = self.collection.find_one({'email': email})
        
        if existing_subscriber:
            # Update existing subscriber
            self.update_subscriber(email, topics, frequency)
            return self.render_home(success='Preferences updated successfully!')
        else:
            # Create new subscriber
            self.save_subscriber(email, topics, frequency)
            return self.render_home(success='Sign up successful! Check your email for confirmation.')

    def handle_optout(self) -> str:
        """
        Handle the opt-out form submission.

        :return: Redirect to homepage after opt-out or render an error
        """
        email = request.form.get('email', '').strip()

        if not self.is_valid_email(email):
            return self.render_home(error='Invalid email address.')

        self.remove_email(email)
        return self.render_home(success='You have been unsubscribed.')

    def handle_get_sign_ups(self) -> dict:
        """
        Retrieve all signed-up users with their preferences.

        :return: List of subscribers with preferences
        """
        subscribers = self.collection.find({}, {'_id': 0})
        return {"subscribers": list(subscribers)}

    def render_preferences(self, token: str) -> str:
        """
        Render preferences page for a specific token.
        
        :param token: Secure token for the subscriber
        :return: Rendered preferences page or error
        """
        subscriber = self.collection.find_one({'preferences_token': token})
        
        if not subscriber:
            return render_template('error.html', 
                                 message='Invalid or expired link.')
        
        return render_template('preferences.html',
                             email=subscriber['email'],
                             topics=self.TOPICS,
                             current_topics=subscriber.get('topics', []),
                             current_frequency=subscriber.get('frequency', 'immediate'),
                             token=token)

    def handle_update_preferences(self, token: str) -> str:
        """
        Handle preference updates via secure token.
        
        :param token: Secure token for the subscriber
        :return: Redirect or error message
        """
        subscriber = self.collection.find_one({'preferences_token': token})
        
        if not subscriber:
            return render_template('error.html', 
                                 message='Invalid or expired link.')
        
        topics = request.form.getlist('topics')
        frequency = request.form.get('frequency', 'immediate')
        
        if not topics:
            return render_template('preferences.html',
                                 email=subscriber['email'],
                                 topics=self.TOPICS,
                                 current_topics=subscriber.get('topics', []),
                                 current_frequency=subscriber.get('frequency', 'immediate'),
                                 token=token,
                                 error='Please select at least one topic.')
        
        self.update_subscriber(subscriber['email'], topics, frequency)
        
        return render_template('preferences.html',
                             email=subscriber['email'],
                             topics=self.TOPICS,
                             current_topics=topics,
                             current_frequency=frequency,
                             token=token,
                             success='Preferences updated successfully!')

    def save_subscriber(self, email: str, topics: list, frequency: str) -> None:
        """
        Save a new subscriber with preferences.

        :param email: Email address to save
        :param topics: List of selected topics
        :param frequency: Notification frequency preference
        """
        try:
            self.collection.insert_one({
                'email': email,
                'topics': topics,
                'frequency': frequency,
                'preferences_token': secrets.token_urlsafe(32),
                'subscription_date': datetime.utcnow(),
                'last_updated': datetime.utcnow()
            })
        except DuplicateKeyError:
            # If email exists, update instead
            self.update_subscriber(email, topics, frequency)

    def update_subscriber(self, email: str, topics: list, frequency: str) -> None:
        """
        Update existing subscriber preferences.
        
        :param email: Email address
        :param topics: List of selected topics
        :param frequency: Notification frequency preference
        """
        self.collection.update_one(
            {'email': email},
            {
                '$set': {
                    'topics': topics,
                    'frequency': frequency,
                    'last_updated': datetime.utcnow()
                }
            }
        )

    def remove_email(self, email: str) -> None:
        """
        Remove the email from the newsletter list.

        :param email: Email address to remove
        """
        self.collection.delete_one({'email': email})

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Validate the provided email address using regex.

        :param email: The email address to validate
        :return: True if valid, False otherwise
        """
        # Regular expression for validating an Email
        email_pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        return re.match(email_pattern, email) is not None

    def email_exists(self, email: str) -> bool:
        """
        Check if the email already exists in the newsletter list.

        :param email: Email address to check
        :return: True if exists, False otherwise
        """
        return self.collection.count_documents({'email': email}) > 0

    def run(self) -> None:
        """
        Run the Flask application.
        """
        # Print warning if using default credentials
        if self.ADMIN_USERNAME == 'admin' or self.ADMIN_PASSWORD == 'changeme':
            print("WARNING: Using default admin credentials. Set ADMIN_USERNAME and ADMIN_PASSWORD environment variables!")
        
        self.app.run(host='0.0.0.0', debug=True)

if __name__ == '__main__':
    app = NewsletterApp()
    app.run()