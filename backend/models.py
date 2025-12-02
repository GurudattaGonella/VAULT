from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Initialize SQLAlchemy (We will connect this in app.py)
db = SQLAlchemy()

# --- 1. User Table (Authentication) ---
class User(UserMixin, db.Model):
    """Stores user accounts and password hashes."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Relationships for history tracking
    documents = db.relationship('Document', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

# --- 2. Document Table (History Tracking) ---
class Document(db.Model):
    """Stores a record of every document uploaded by a user."""
    id = db.Column(db.Integer, primary_key=True)
    
    # The display name for the user
    filename = db.Column(db.String(255), nullable=False)
    
    # The unique ID used to retrieve this document's vectors from ChromaDB
    chroma_collection_id = db.Column(db.String(255), unique=True, nullable=False)
    
    # Used for displaying "Last 10 Uploads"
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Link to the User who uploaded it
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Document {self.filename} - User {self.user_id}>'