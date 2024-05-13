from app import app, db
from models import Image, Annotation
import os


def add_images_to_db(folder_path):
    for entry in os.scandir(folder_path):
        if entry.is_file() and entry.name.endswith(('.jpg', '.png')):
            print(f"Debug: {entry}")
            with open(entry.path, 'rb') as file:
                image_data = file.read()
                new_image = Image(image_name=entry.name, image_data=image_data)
                db.session.add(new_image)
                db.session.flush()

                annotation_files = [f for f in os.listdir(folder_path) if f.startswith(entry.name.split('.')[0]) and f.endswith('.txt')]
                for annotation_file in annotation_files:
                    with open(os.path.join(folder_path, annotation_file), 'r') as af:
                        annotation_data = af.read()
                        new_annotation = Annotation(image_id=new_image.id, annotation_data=annotation_data)
                        db.session.add(new_annotation)

    db.session.commit()
    print(f"Images and annotations added to the database from {folder_path}")


if __name__ == '__main__':
    folder_path = './uploads/folder3'
    with app.app_context():
        add_images_to_db(folder_path)
