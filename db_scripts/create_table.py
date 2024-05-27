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
                ['image_id', 'upper_label', 'lower_label', 'shoe_label',
                 'upper_label_x', 'upper_label_y', 'upper_label_width',
                 'upper_label_height',
                 'lower_label_x', 'lower_label_y', 'lower_label_width',
                 'lower_label_height'])

            labels = Label.query.join(Image, Label.image_id == Image.id).all()

            for label in labels:
                writer.writerow([
                    label.image_id, label.upper_label, label.lower_label,
                    label.shoe_label,
                    label.upper_label_x, label.upper_label_y,
                    label.upper_label_width, label.upper_label_height,
                    label.lower_label_x, label.lower_label_y,
                    label.lower_label_width, label.lower_label_height
                ])


if __name__ == '__main__':
    reset_database()
    # export_data_to_csv()

