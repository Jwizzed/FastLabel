from app import app, db
from models import Image, IsUseGroupId
import os
import re


def extract_group_number(filename):
    match = re.search(r'group(\d+)', filename)
    if match:
        return int(match.group(1))
    return None

def add_images_to_db(folder_path):
    groups_id = []
    for entry in os.scandir(folder_path):
        if entry.is_file() and entry.name.endswith(('.jpg', '.png')):
            image_path = entry.path
            group_id = extract_group_number(entry.name)
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                new_image = Image(image_name=entry.name, image_data=image_data, group_id=group_id)
                db.session.add(new_image)
                db.session.flush()
                if group_id not in groups_id:
                    new_group_id = IsUseGroupId(group_id=group_id)
                    db.session.add(new_group_id)
                    db.session.flush()
                    groups_id.append(group_id)
    db.session.commit()
    print(f"Images and annotations added to the database from {folder_path}")

if __name__ == '__main__':
    folder_path = '../test_image'
    with app.app_context():
        add_images_to_db(folder_path)
