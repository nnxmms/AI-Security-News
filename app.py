#!/usr/bin/python3

from flask import Flask, render_template, request, redirect, url_for, Blueprint

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

    def render_home(self) -> str:
        """
        Render the homepage template.

        :return: Rendered HTML of the homepage
        """
        return render_template('home.html')

    def handle_signup(self) -> str:
        """
        Handle the signup form submission.

        :return: Redirect to homepage after signup
        """
        email: str = request.form['email']
        self.save_email(email)
        return redirect(url_for('.home'))  # Use the Blueprint's context

    def handle_optout(self) -> str:
        """
        Handle the opt-out form submission.

        :return: Redirect to homepage after opt-out
        """
        email: str = request.form['email']
        self.remove_email(email)
        return redirect(url_for('.home'))  # Use the Blueprint's context

    def save_email(self, email: str) -> None:
        """
        Save the email to the newsletter list.

        :param email: Email address to save
        """
        # Implementation to save email
        pass

    def remove_email(self, email: str) -> None:
        """
        Remove the email from the newsletter list.

        :param email: Email address to remove
        """
        # Implementation to remove email
        pass

    def run(self) -> None:
        """
        Run the Flask application.
        """
        self.app.run(host='0.0.0.0', debug=True)

if __name__ == '__main__':
    app = NewsletterApp()
    app.run()