from werkzeug.security import generate_password_hash, check_password_hash

# --- Password Hashing Functions ---

def set_password(password):
    """Hashes the plain text password for secure storage."""
    # We use sha256 hashing algorithm
    return generate_password_hash(password, method='pbkdf2:sha256')

def check_password(hashed_password, password):
    """Checks the stored hash against a provided plain text password."""
    return check_password_hash(hashed_password, password)

# --- Other Utility Functions (For Future Use) ---

def is_valid_username(username):
    """Basic validation for username format."""
    return 3 <= len(username) <= 20 and username.isalnum()

def is_valid_password(password):
    """Basic validation for password complexity."""
    return len(password) >= 8