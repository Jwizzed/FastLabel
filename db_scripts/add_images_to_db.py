from app import app, db
from models import Image, Annotation
import os


def add_images_to_db(folder_path):
    for entry in os.scandir(folder_path):
        if entry.is_file() and entry.name.endswith(('.jpg', '.png')):
            image_path = entry.path
            annotation_path = image_path.rsplit(".", 1)[0]+".txt"
            print(annotation_path)
            if os.path.exists(annotation_path):
                print(annotation_path, "is Valid.")
                with open(image_path, 'rb') as image_file:
                    image_data = image_file.read()
                    new_image = Image(image_name=entry.name, image_data=image_data)
                    db.session.add(new_image)
                    db.session.flush()

                with open(annotation_path, 'r') as annotation_file:
                    annotation_data = annotation_file.read()
                    new_annotation = Annotation(image_id=new_image.id, annotation_data=annotation_data)
                    db.session.add(new_annotation)
                print(f"Added image and annotation for {entry.name}")

    db.session.commit()
    print(f"Images and annotations added to the database from {folder_path}")


if __name__ == '__main__':
    folder_path = './uploads/folder3'
    with app.app_context():
        add_images_to_db(folder_path)
