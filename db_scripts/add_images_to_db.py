from app import app, db
from models import Image  #, Annotation
import os


def add_images_to_db(folder_path):
    for entry in os.scandir(folder_path):
        if entry.is_file() and entry.name.endswith(('.jpg', '.png')):
            image_path = entry.path
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                new_image = Image(image_name=entry.name, image_data=image_data)
                db.session.add(new_image)
                db.session.flush()

    db.session.commit()
    print(f"Images and annotations added to the database from {folder_path}")


if __name__ == '__main__':
    folder_path = './uploads/folder3'
    with app.app_context():
        add_images_to_db(folder_path)
