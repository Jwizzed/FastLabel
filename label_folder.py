from flask import Blueprint, render_template, redirect, url_for, request, session
from models import Image, Label, SkippedImage, Annotation
import cv2
import numpy as np
import base64
from app import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.label_images'))

@main.route('/label', methods=['GET', 'POST'])
def label_images():
    image = Image.query \
        .outerjoin(SkippedImage, Image.id == SkippedImage.image_id) \
        .filter(SkippedImage.id.is_(None)) \
        .first()

    if not image:
        return render_template('unlabeled.html')

    image_data = cv2.imdecode(np.frombuffer(image.image_data, np.uint8),
                              cv2.IMREAD_COLOR)
    annotated_image = image_data.copy()
    original_height, original_width = annotated_image.shape[:2]
    annotations = Annotation.query.filter_by(image_id=image.id).all()
    print("DEBUG:")
    print(annotations)

    upper_label_xy = None
    lower_label_xy = None

    for set_annotation in annotations:
        for annotation in set_annotation.annotation_data.split("\n")[:-1]:
            class_id, x_center, y_center, width, height = map(float, annotation.split())
            x1 = int((x_center - width / 2) * original_width)
            y1 = int((y_center - height / 2) * original_height)
            x2 = int((x_center + width / 2) * original_width)
            y2 = int((y_center + height / 2) * original_height)

            if upper_label_xy is None or y1 < upper_label_xy[1]:
                upper_label_xy = [x1, y1, x2, y2]
            else:
                lower_label_xy = [x1, y1, x2, y2]

    annotated_image = resize_image(annotated_image)
    resized_height, resized_width = annotated_image.shape[:2]

    for label_xy in [upper_label_xy, lower_label_xy]:
        if label_xy:
            x1, y1, x2, y2 = label_xy
            x1_resized = int(x1 * resized_width / original_width)
            y1_resized = int(y1 * resized_height / original_height)
            x2_resized = int(x2 * resized_width / original_width)
            y2_resized = int(y2 * resized_height / original_height)
            cv2.rectangle(annotated_image, (x1_resized, y1_resized), (x2_resized, y2_resized), (0, 255, 0), 2)

    if request.method == 'POST':
        if 'skip' in request.form:
            skipped_image = SkippedImage(image_id=image.id)
            db.session.add(skipped_image)
            db.session.commit()
            session.clear()
            return redirect(url_for('main.label_images'))

        print("Process label form:", request.form['choice'])
        process_label_form(request, image, upper_label_xy, lower_label_xy)

    question, choices = get_label_questions()
    encoded_image = base64.b64encode(cv2.imencode('.jpg', annotated_image)[1]).decode('utf-8')
    return render_template('label.html', image=encoded_image, question=question, choices=choices)


def get_label_questions():
    if 'upper_label' not in session:
        return 'Select the upper cloth:', ['Polo', 'Long sleeve T-shirt', 'Long sleeve shirt', 'Short sleeve Shirt', 'Short sleeve T-shirt',
                                           'Sleeveless', 'Long sleeve blouse', 'Short sleeve blouse', 'Dress', 'Outwear']
    elif 'lower_label' not in session:
        return 'Select the lower cloth:', ['Trousers', 'Shorts', 'Skirt']
    else:
        return 'Select the shoes:', ['Sandals', 'Sneakers', 'High heels', 'Leather shoes', 'None']


def process_label_form(request, image, upper_label_xy, lower_label_xy):
    choice = request.form['choice']
    if 'upper_label' not in session:
        session['upper_label'] = choice
        print("Assign upper session with:", choice)
    elif 'lower_label' not in session:
        print("In Lower Label")
        session['lower_label'] = choice
    else:
        session['shoe_label'] = choice
        save_labels_to_db(image, session, upper_label_xy, lower_label_xy)
        session.clear()
        return redirect(url_for('main.label_images'))


def save_labels_to_db(image, session_info, upper_label_xy, lower_label_xy):
    label = Label(
        image_id=image.id,
        upper_label=session_info['upper_label'],
        lower_label=session_info['lower_label'],
        shoe_label=session_info['shoe_label'],
        upper_label_x=upper_label_xy[0] if upper_label_xy else None,
        upper_label_y=upper_label_xy[1] if upper_label_xy else None,
        upper_label_width=upper_label_xy[2] - upper_label_xy[0] if upper_label_xy else None,
        upper_label_height=upper_label_xy[3] - upper_label_xy[1] if upper_label_xy else None,
        lower_label_x=lower_label_xy[0] if lower_label_xy else None,
        lower_label_y=lower_label_xy[1] if lower_label_xy else None,
        lower_label_width=lower_label_xy[2] - lower_label_xy[0] if lower_label_xy else None,
        lower_label_height=lower_label_xy[3] - lower_label_xy[1] if lower_label_xy else None
    )
    db.session.add(label)
    db.session.commit()


def resize_image(image, max_width=800, max_height=400):
    height, width = image.shape[:2]
    if width > max_width or height > max_height:
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        resized_image = cv2.resize(image, (new_width, new_height))
        return resized_image
    else:
        return image
