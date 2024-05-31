import csv
from app import app, db
from sqlalchemy import text
from models import Image, Label


def create_database():
    with app.app_context():
        db.create_all()


def reset_database():
    with app.app_context():
        db.session.execute(text('DROP TABLE IF EXISTS annotation CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS label CASCADE;'))  # Add this if 'label' also depends on 'image'
        db.session.execute(text('DROP TABLE IF EXISTS skipped_image CASCADE;'))  # Assuming 'skipped_image' might also depend on 'image'
        db.session.execute(text('DROP TABLE IF EXISTS image CASCADE;'))  # Now safe to drop 'image'
        db.session.commit()
        db.create_all()
        print("Database has been reset and new tables have been created.")


def export_data_to_csv():
    with app.app_context():
        csv_file_path = 'exported_labels.csv'

        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow(
                ['image_id', 'age', 'gender', 'hair_length',
                 'upper_body_length', 'upper_body_color', 'lower_body_length',
                 'lower_body_color',
                 'lower_body_type', 'backpack', 'bag',
                 'glasses', 'hat'])

            labels = Label.query.join(Image, Label.image_id == Image.id).all()

            for label in labels:
                writer.writerow([
                    label.image_id, label.age, label.gender,
                    label.hair_length,
                    label.upper_body_length, label.upper_body_color,
                    label.lower_body_length, label.lower_body_color,
                    label.lower_body_type, label.backpack,
                    label.bag, label.glasses, label.hat
                ])


if __name__ == '__main__':
    reset_database()
    # export_data_to_csv()

