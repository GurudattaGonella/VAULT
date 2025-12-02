# init_db.py
from app import app, db

print("🔄 Connecting to database...")

with app.app_context():
    print("🔨 Building tables...")
    db.create_all()
    print("✅ SUCCESS: 'vault.db' has been created!")