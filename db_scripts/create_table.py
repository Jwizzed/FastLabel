from app import app, db


def create_database():
    with app.app_context():
        db.create_all()


def reset_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database has been reset and new tables have been created.")


if __name__ == '__main__':
    reset_database()
