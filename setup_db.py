from app import db, app
import os
from alembic import op
from sqlalchemy import engine, Column, String, Integer
from sqlalchemy.exc import OperationalError

with app.app_context():
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].split("///")[-1]
    
    if not os.path.exists(db_path):
        db.create_all()
