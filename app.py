#!/usr/bin/python3

from flask import Flask, render_template, request, redirect, url_for, Blueprint, jsonify, Response
from flask_mail import Mail, Message
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
import re
import secrets
import os
from functools import wraps
from typing import List, Dict, Optional

class NewsletterApp:
    """
    This class implements a newsletter signup web application with topic preferences and paper library.
    """

    def __init__(self) -> None:
        """
        Initialize NewsletterApp.
        """
        # Flask app
        self.app: Flask = Flask(__name__)
        
        # Mail configuration from environment variables
        self.app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
        self.app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
        self.app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
        self.app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
        self.app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
        self.app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@hacking-and-security.de')
        
        # Initialize Flask-Mail
        self.mail = Mail(self.app)
        
        # Create a Blueprint for the newsletter
        self.newsletter_bp = Blueprint('newsletter', __name__, url_prefix='/newsletter')
        # MongoDB setup
        self.client = MongoClient('mongodb://newsletter-db-1:27017/')
        self.db = self.client['newsletter_db']
        self.collection = self.db['subscribers']
        self.papers_collection = self.db['papers']

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

        # Create indexes for better performance
        self.collection.create_index('email', unique=True)
        self.collection.create_index('verification_token')
        self.collection.create_index('preferences_token')
        self.papers_collection.create_index('arxiv-id', unique=True)
        self.papers_collection.create_index('published')
        self.papers_collection.create_index([('title', 'text'), ('abstract', 'text'), ('authors', 'text')])

    def setup_routes(self) -> None:
        """
        Setup Flask application routes.
        """
        # Route for the homepage
        @self.newsletter_bp.route('/', methods=['GET'])
        def home():
            return self.render_home()

        # Route for email verification
        @self.newsletter_bp.route('/verify/<token>', methods=['GET'])
        def verify_email(token):
            return self.handle_email_verification(token)

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

        # Route for storing papers (authenticated)
        @self.newsletter_bp.route('/store-paper', methods=['POST'])
        @self.requires_auth
        def store_paper():
            return self.handle_store_paper()

        # Route for the paper library
        @self.newsletter_bp.route('/library', methods=['GET'])
        def library():
            return self.render_library()

        # Route for individual paper details
        @self.newsletter_bp.route('/paper/<arxiv_id>', methods=['GET'])
        def paper_detail(arxiv_id):
            return self.render_paper_detail(arxiv_id)

        # Route for preferences management page (via secure token)
        @self.newsletter_bp.route('/preferences/<token>', methods=['GET'])
        def preferences(token):
            return self.render_preferences(token)

        # Route for updating preferences via token
        @self.newsletter_bp.route('/preferences/<token>', methods=['POST'])
        def update_preferences(token):
            return self.handle_update_preferences(token)
            
        # Route for unsubscribe via token
        @self.newsletter_bp.route('/unsubscribe/<token>', methods=['GET', 'POST'])
        def unsubscribe(token):
            return self.handle_unsubscribe(token)
        
        # Route for sending preferences link to existing users
        @self.newsletter_bp.route('/send-preferences-link', methods=['POST'])
        def send_preferences_link():
            return self.handle_send_preferences_link()

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

    def handle_email_verification(self, token: str) -> str:
        """
        Handle email verification via token.
        
        :param token: Verification token
        :return: Rendered template or redirect
        """
        subscriber = self.collection.find_one({'verification_token': token})
        
        if not subscriber:
            return render_template('error.html', 
                                 message='Invalid or expired verification link.')
        
        if subscriber.get('verified', False):
            return self.render_preferences(subscriber['preferences_token'])
        
        # Mark as verified and remove verification token
        self.collection.update_one(
            {'_id': subscriber['_id']},
            {
                '$set': {'verified': True},
                '$unset': {'verification_token': ''}
            }
        )
        
        return self.render_preferences(subscriber['preferences_token'])

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
            if not existing_subscriber.get('verified', False):
                # Resend verification email
                try:
                    self.send_verification_email(email, topics, frequency, existing_subscriber.get('verification_token'))
                    return self.render_home(success='Verification email sent! Please check your inbox.')
                except Exception as e:
                    return self.render_home(error='Failed to send verification email. Please try again.')
            else:
                return self.render_home(error='Email already registered. Use the link in your newsletter emails to manage preferences.')
        else:
            # Create new unverified subscriber and send verification email
            try:
                verification_token = self.save_unverified_subscriber(email, topics, frequency)
                self.send_verification_email(email, topics, frequency, verification_token)
                return self.render_home(success='Verification email sent! Please check your inbox and click the verification link.')
            except Exception as e:
                return self.render_home(error='Failed to process signup. Please try again.')

    def handle_optout(self) -> str:
        """
        Handle the opt-out form submission.

        :return: Redirect to homepage after opt-out or render an error
        """
        return self.render_home(error='Direct unsubscribe is no longer available. Please use the unsubscribe link in your newsletter emails.')

    def handle_get_sign_ups(self) -> dict:
        """
        Retrieve all verified signed-up users and users signed up before 2025-05-30 with their preferences.

        :return: List of subscribers with preferences
        """
        # Hardcoded cutoff date: 2025-05-30 00:00:00 UTC
        cutoff_date = datetime(2025, 5, 30, 0, 0, 0)
        
        # Query for verified users OR users signed up before 2025-05-30
        query = {
            '$or': [
                {'verified': True},
                {'subscription_date': {'$lt': cutoff_date}}
            ]
        }
        
        subscribers = self.collection.find(query, {'_id': 0})
        return {"subscribers": list(subscribers)}

    def handle_store_paper(self) -> dict:
        """
        Store a paper in the papers collection.
        
        :return: JSON response indicating success or failure
        """
        try:
            paper_data = request.get_json()
            
            if not paper_data:
                return jsonify({'success': False, 'error': 'No paper data provided'}), 400
            
            # Required fields
            required_fields = ['arxiv-id', 'title', 'abstract', 'authors', 'published']
            for field in required_fields:
                if field not in paper_data:
                    return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
            
            # Add storage timestamp
            paper_data['stored_at'] = datetime.utcnow()
            
            # Optional AI analysis fields
            analysis_fields = ['key_points', 'conclusion', 'relevance_explanation']
            for field in analysis_fields:
                if field not in paper_data:
                    paper_data[field] = None
            
            # Try to insert the paper
            try:
                self.papers_collection.insert_one(paper_data)
                return jsonify({'success': True, 'message': 'Paper stored successfully'})
            except DuplicateKeyError:
                # Paper already exists, update it
                self.papers_collection.replace_one(
                    {'arxiv-id': paper_data['arxiv-id']},
                    paper_data
                )
                return jsonify({'success': True, 'message': 'Paper updated successfully'})
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    def render_library(self) -> str:
        """
        Render the paper library page with search and filtering.
        
        :return: Rendered HTML of the library page
        """
        # Get search and filter parameters
        search_query = request.args.get('search', '').strip()
        topic_filter = request.args.get('topic', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 24  # Cards per page
        
        # Build MongoDB query
        query = {}
        
        # Add search functionality
        if search_query:
            query['$text'] = {'$search': search_query}
        
        # Add topic filter
        if topic_filter and topic_filter in ['red_teaming', 'safety', 'governance']:
            query['relevant_for'] = topic_filter
        
        # Get total count for pagination
        total_papers = self.papers_collection.count_documents(query)
        
        # Get papers with pagination - only fields needed for library view
        skip = (page - 1) * per_page
        papers_cursor = self.papers_collection.find(
            query, 
            {
                'arxiv-id': 1, 
                'title': 1, 
                'published': 1, 
                'relevant_for': 1, 
                'authors': 1
            }
        ).sort('published', -1).skip(skip).limit(per_page)
        papers = list(papers_cursor)
        
        # Group papers by week
        grouped_papers = self.group_papers_by_week(papers)
        
        # Calculate pagination info
        total_pages = (total_papers + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('library.html',
                             grouped_papers=grouped_papers,
                             topics=self.TOPICS,
                             search_query=search_query,
                             topic_filter=topic_filter,
                             page=page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next,
                             total_papers=total_papers)

    def group_papers_by_week(self, papers: List[Dict]) -> List[Dict]:
        """
        Group papers by week based on published date.
        
        :param papers: List of paper documents
        :return: List of week groups with papers
        """
        weeks = {}
        
        for paper in papers:
            try:
                # Parse published date
                if isinstance(paper.get('published'), str):
                    pub_date = datetime.fromisoformat(paper['published'].replace('Z', '+00:00'))
                else:
                    pub_date = paper.get('published', datetime.utcnow())
                
                # Calculate week start (Monday)
                days_since_monday = pub_date.weekday()
                week_start = pub_date - timedelta(days=days_since_monday)
                week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                
                week_key = week_start.isoformat()
                
                if week_key not in weeks:
                    weeks[week_key] = {
                        'week_start': week_start,
                        'week_end': week_start + timedelta(days=6),
                        'papers': []
                    }
                
                weeks[week_key]['papers'].append(paper)
                
            except Exception as e:
                # If date parsing fails, put in current week
                current_week_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                days_since_monday = current_week_start.weekday()
                current_week_start = current_week_start - timedelta(days=days_since_monday)
                
                week_key = current_week_start.isoformat()
                
                if week_key not in weeks:
                    weeks[week_key] = {
                        'week_start': current_week_start,
                        'week_end': current_week_start + timedelta(days=6),
                        'papers': []
                    }
                
                weeks[week_key]['papers'].append(paper)
        
        # Convert to sorted list (newest first)
        sorted_weeks = sorted(weeks.values(), key=lambda x: x['week_start'], reverse=True)
        
        return sorted_weeks

    def render_paper_detail(self, arxiv_id: str) -> str:
        """
        Render individual paper detail page.
        
        :param arxiv_id: arXiv ID of the paper
        :return: Rendered HTML of the paper detail page
        """
        # Find the paper by arxiv-id
        paper = self.papers_collection.find_one({'arxiv-id': arxiv_id})
        
        if not paper:
            return render_template('error.html', 
                                 message='Paper not found.')
        
        return render_template('paper_detail.html',
                             paper=paper,
                             topics=self.TOPICS)

    def group_papers_by_week(self, papers: List[Dict]) -> List[Dict]:
        """
        Group papers by week based on published date.
        
        :param papers: List of paper documents
        :return: List of week groups with papers
        """
        weeks = {}
        
        for paper in papers:
            try:
                # Parse published date
                if isinstance(paper.get('published'), str):
                    pub_date = datetime.fromisoformat(paper['published'].replace('Z', '+00:00'))
                else:
                    pub_date = paper.get('published', datetime.utcnow())
                
                # Calculate week start (Monday)
                days_since_monday = pub_date.weekday()
                week_start = pub_date - timedelta(days=days_since_monday)
                week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                
                week_key = week_start.isoformat()
                
                if week_key not in weeks:
                    weeks[week_key] = {
                        'week_start': week_start,
                        'week_end': week_start + timedelta(days=6),
                        'papers': []
                    }
                
                weeks[week_key]['papers'].append(paper)
                
            except Exception as e:
                # If date parsing fails, put in current week
                current_week_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                days_since_monday = current_week_start.weekday()
                current_week_start = current_week_start - timedelta(days=days_since_monday)
                
                week_key = current_week_start.isoformat()
                
                if week_key not in weeks:
                    weeks[week_key] = {
                        'week_start': current_week_start,
                        'week_end': current_week_start + timedelta(days=6),
                        'papers': []
                    }
                
                weeks[week_key]['papers'].append(paper)
        
        # Convert to sorted list (newest first)
        sorted_weeks = sorted(weeks.values(), key=lambda x: x['week_start'], reverse=True)
        
        return sorted_weeks

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
        
        # Check if verified OR signed up before cutoff date
        cutoff_date = datetime(2025, 5, 30, 0, 0, 0)
        is_verified = subscriber.get('verified', False)
        is_legacy_user = subscriber.get('subscription_date', datetime.utcnow()) < cutoff_date
        
        if not is_verified and not is_legacy_user:
            return render_template('error.html', 
                                 message='Please verify your email address first.')
        
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
        
        # Check if verified OR signed up before cutoff date
        cutoff_date = datetime(2025, 5, 30, 0, 0, 0)
        is_verified = subscriber.get('verified', False)
        is_legacy_user = subscriber.get('subscription_date', datetime.utcnow()) < cutoff_date
        
        if not is_verified and not is_legacy_user:
            return render_template('error.html', 
                                 message='Please verify your email address first.')
        
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

    def handle_unsubscribe(self, token: str) -> str:
        """
        Handle unsubscribe via token.
        
        :param token: Preferences token
        :return: Rendered template or redirect
        """
        subscriber = self.collection.find_one({'preferences_token': token})
        
        if not subscriber:
            return render_template('error.html', 
                                 message='Invalid or expired unsubscribe link.')
        
        if request.method == 'POST':
            # Actually unsubscribe
            self.remove_email(subscriber['email'])
            return render_template('success.html', 
                                 message='You have been successfully unsubscribed from the AI Security Newsletter.')
        
        # Show confirmation page
        return render_template('preferences.html',
                             email=subscriber['email'],
                             topics=self.TOPICS,
                             current_topics=subscriber.get('topics', []),
                             current_frequency=subscriber.get('frequency', 'immediate'),
                             token=token,
                             show_unsubscribe=True)

    def handle_send_preferences_link(self) -> str:
        """
        Handle sending preferences link to existing users.
        
        :return: Rendered home page with success/error message
        """
        email = request.form.get('email', '').strip()
        
        if not self.is_valid_email(email):
            return self.render_home(error='Invalid email address.')
        
        # Find the subscriber
        subscriber = self.collection.find_one({'email': email})
        
        if not subscriber:
            return self.render_home(error='Email address not found. Please sign up first.')
        
        # Check if verified OR signed up before cutoff date
        cutoff_date = datetime(2025, 5, 30, 0, 0, 0)
        is_verified = subscriber.get('verified', False)
        is_legacy_user = subscriber.get('subscription_date', datetime.utcnow()) < cutoff_date
        
        if not is_verified and not is_legacy_user:
            return self.render_home(error='Please verify your email address first using the link sent during signup.')
        
        # Generate preferences token if it doesn't exist
        preferences_token = subscriber.get('preferences_token')
        if not preferences_token:
            preferences_token = secrets.token_urlsafe(32)
            self.collection.update_one(
                {'email': email},
                {'$set': {'preferences_token': preferences_token}}
            )
        
        try:
            # Send preferences email
            self.send_preferences_email(email, preferences_token)
            return self.render_home(success='Preferences link sent! Please check your inbox.')
        except Exception as e:
            return self.render_home(error='Failed to send preferences link. Please try again.')

    def save_unverified_subscriber(self, email: str, topics: list, frequency: str) -> str:
        """
        Save a new unverified subscriber with preferences.

        :param email: Email address to save
        :param topics: List of selected topics
        :param frequency: Notification frequency preference
        :return: Verification token
        """
        verification_token = secrets.token_urlsafe(32)
        preferences_token = secrets.token_urlsafe(32)
        
        try:
            self.collection.insert_one({
                'email': email,
                'topics': topics,
                'frequency': frequency,
                'verified': False,
                'verification_token': verification_token,
                'preferences_token': preferences_token,
                'subscription_date': datetime.utcnow(),
                'last_updated': datetime.utcnow()
            })
            return verification_token
        except DuplicateKeyError:
            # If email exists, update the verification token
            self.collection.update_one(
                {'email': email},
                {
                    '$set': {
                        'topics': topics,
                        'frequency': frequency,
                        'verification_token': verification_token,
                        'last_updated': datetime.utcnow()
                    }
                }
            )
            return verification_token

    def send_verification_email(self, email: str, topics: list, frequency: str, verification_token: str) -> None:
        """
        Send verification email to the subscriber.
        
        :param email: Email address
        :param topics: Selected topics
        :param frequency: Notification frequency
        :param verification_token: Verification token
        """
        # Create verification link
        verification_link = url_for('newsletter.verify_email', token=verification_token, _external=True)
        
        # Convert topic IDs to names
        topic_names = [self.TOPICS.get(topic, topic) for topic in topics]
        
        # Render email template
        html_body = render_template('verification_email.html',
                                   verification_link=verification_link,
                                   topics=topic_names,
                                   frequency=frequency.title())
        
        # Create and send email
        msg = Message(
            subject='Verify Your Email - AI Security News',
            recipients=[email],
            html=html_body
        )
        
        self.mail.send(msg)

    def send_preferences_email(self, email: str, preferences_token: str) -> None:
        """
        Send preferences link email to existing subscriber.
        
        :param email: Email address
        :param preferences_token: Preferences token
        """
        # Create preferences link
        preferences_link = url_for('newsletter.preferences', token=preferences_token, _external=True)
        
        # Render email template
        html_body = render_template('preferences_email.html',
                                   preferences_link=preferences_link)
        
        # Create and send email
        msg = Message(
            subject='Your Newsletter Preferences - AI Security News',
            recipients=[email],
            html=html_body
        )
        
        self.mail.send(msg)

    def save_subscriber(self, email: str, topics: list, frequency: str) -> None:
        """
        Save a new verified subscriber with preferences.

        :param email: Email address to save
        :param topics: List of selected topics
        :param frequency: Notification frequency preference
        """
        try:
            self.collection.insert_one({
                'email': email,
                'topics': topics,
                'frequency': frequency,
                'verified': True,
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