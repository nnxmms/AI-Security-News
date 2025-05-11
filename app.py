#!/usr/bin/python3

from flask import Flask, render_template, request, redirect, url_for, Blueprint
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import re

class NewsletterApp:
    """
    This class implements a simple newsletter signup web application.
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
        self.client = MongoClient('mongodb://newsletter-db-1:27017/')  # Adjust the URI as needed
        self.db = self.client['newsletter_db']  # Database name
        self.collection = self.db['subscribers']  # Collection name

        # Setup routes
        self.setup_routes()

        # Register the Blueprint
        self.app.register_blueprint(self.newsletter_bp)

    def setup_routes(self) -> None:
        """
        Setup Flask application routes.
        """
        # Route for the homepage
        @self.newsletter_bp.route('/', methods=['GET'])
        def home():
            return self.render_home()

        # Route for the signup form
        @self.newsletter_bp.route('/signup', methods=['POST'])
        def signup():
            return self.handle_signup()

        # Route for the opt-out form
        @self.newsletter_bp.route('/optout', methods=['POST'])
        def optout():
            return self.handle_optout()

        # Route to get all new sign-ups
        @self.newsletter_bp.route('/fb0454df-1b01-48fa-9b1e-58d4d3c282ac-6911e296-dc31-4afc-b9ed-f03bfc7d879b', methods=['GET'])
        def get_sign_ups():
            return self.handle_get_sign_ups()

    def render_home(self, error=None) -> str:
        """
        Render the homepage template.

        :return: Rendered HTML of the homepage
        """
        return render_template('home.html', error=error)

    def handle_signup(self) -> str:
        """
        Handle the signup form submission.

        :return: Redirect to homepage after signup or render an error
        """
        email: str = request.form['email']

        if not self.is_valid_email(email):
            return self.render_home(error='Invalid email address.')

        self.save_email(email)
        self.render_home(success='Sign up successful!')

    def handle_optout(self) -> str:
        """
        Handle the opt-out form submission.

        :return: Redirect to homepage after opt-out or render an error
        """
        email: str = request.form['email']

        if not self.is_valid_email(email):
            return self.render_home(error='Invalid email address.')

        self.remove_email(email)
        self.render_home(success='Opt out successful!')

    def handle_get_sign_ups(self) -> str:
        """
        Retrieve all signed-up users.

        :return: List of emails signed up
        """
        subscribers = self.collection.find({}, {'_id': 0, 'email': 1})
        emails = [sub['email'] for sub in subscribers]
        return {"subscribers": emails}

    def save_email(self, email: str) -> None:
        """
        Save the email to the newsletter list.

        :param email: Email address to save
        """
        try:
            self.collection.insert_one({'email': email})
        except DuplicateKeyError:
            # Email already in the database, handle accordingly
            pass

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

    def run(self) -> None:
        """
        Run the Flask application.
        """
        self.app.run(host='0.0.0.0', debug=True)

if __name__ == '__main__':
    app = NewsletterApp()
    app.run()