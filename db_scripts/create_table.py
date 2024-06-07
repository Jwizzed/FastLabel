import csv
from app import app, db
from sqlalchemy import text
from models import Image


def create_database():
    with app.app_context():
        db.create_all()


def reset_database():
    with app.app_context():
        db.session.execute(text('DROP TABLE IF EXISTS image CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS is_use_group_id CASCADE;')) 
        db.session.execute(text('DROP TABLE IF EXISTS is_not_use_group_id CASCADE;'))  
        db.session.commit()
        db.create_all()
        print("Database has been reset and new tables have been created.")

if __name__ == '__main__':
    # create_database()
    reset_database()

