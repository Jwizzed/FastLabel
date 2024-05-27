from flask import Blueprint, render_template, redirect, url_for, request, session
from models import Image, Label, SkippedImage  #, Annotation
from sqlalchemy.sql.expression import func
import cv2
import numpy as np
import base64
from app import db

main = Blueprint('main', __name__)


def initialize_label_questions():
    questions = [
        ('age', 'Select the age group:', ['Young', 'Adult', 'Old']),
        ('gender', 'Select the gender:', ['Male', 'Female']),
        ('hair_length', 'Select hair length:', ['Short', 'Bald', 'Long']),
        ('upper_body_length', 'Select the upper body cloth length:', ['Short', 'Long']),
        ('upper_body_color', 'Select the upper body color:', ['Black', 'Blue', 'Brown', 'Green', 'Grey', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow', 'Other']),
        ('lower_body_length', 'Select the lower body cloth length:', ['Short', 'Long']),
        ('lower_body_color', 'Select the lower body color:', ['Black', 'Blue', 'Brown', 'Green', 'Grey', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow', 'Other']),
        ('lower_body_type', 'Select the lower body type:', ['Trousers&Shorts', 'Skirt&Dress']),
        ('backpack', 'Does the person have a backpack?', ['Yes', 'No']),
        ('bag', 'Does the person have a bag?', ['Yes', 'No']),
        ('glasses', 'Does the person wear glasses?', ['Normal', 'Sun', 'No']),
        ('hat', 'Does the person wear a hat?', ['Yes', 'No'])
    ]
    session['questions'] = questions
    session['current_question'] = 0


@main.route('/')
def index():
    return redirect(url_for('main.label_images'))


@main.route('/label', methods=['GET', 'POST'])
def label_images():
    if 'image_id' in session:
        image_id = session['image_id']
        image = Image.query.get(image_id)
    else:
        image = Image.query.order_by(func.random()).first()
        if image:
            session['image_id'] = image.id
            initialize_label_questions()

    if not image:
        session.pop('image_id', None)
        return render_template('unlabeled.html')

    if request.method == 'POST':
        response = process_label_form(request, image)
        if response:
            return response

    return render_current_image(image)


def render_current_image(image):
    image_data = cv2.imdecode(np.frombuffer(image.image_data, np.uint8), cv2.IMREAD_COLOR)
    annotated_image = image_data.copy()
    annotated_image = resize_image(annotated_image, 800, 400)
    question, choices = get_label_questions()
    encoded_image = base64.b64encode(cv2.imencode('.jpg', annotated_image)[1]).decode('utf-8')
    return render_template('label.html', image=encoded_image, question=question, choices=choices)


def draw_annotations(image, upper_label_xy, lower_label_xy, original_width, original_height):
    resized_height, resized_width = image.shape[:2]
    for label_xy in [upper_label_xy, lower_label_xy]:
        if label_xy:
            x1, y1, x2, y2 = label_xy
            x1_resized = int(x1 * resized_width / original_width)
            y1_resized = int(y1 * resized_height / original_height)
            x2_resized = int(x2 * resized_width / original_width)
            y2_resized = int(y2 * resized_height / original_height)
            cv2.rectangle(image, (x1_resized, y1_resized), (x2_resized, y2_resized), (0, 255, 0), 2)


def get_label_questions():
    if 'current_question' in session:
        question_index = session['current_question']
        questions = session['questions']
        if question_index < len(questions):
            attr, question, choices = questions[question_index]
            return question, choices
    return None, []


def process_label_form(request, image):
    if 'skip' in request.form:
        skipped_image = SkippedImage(image_id=image.id)
        db.session.add(skipped_image)
        db.session.commit()
        session.clear()
        return redirect(url_for('main.label_images'))

    choice = request.form.get('choice')
    if choice:
        attr, _, _ = session['questions'][session['current_question']]
        session[attr] = choice
        session['current_question'] += 1

        if session['current_question'] >= len(session['questions']):
            save_labels_to_db(image, session)
            session.clear()
            return redirect(url_for('main.label_images'))


def save_labels_to_db(image, session_info):
    label = Label(
        image_id=image.id,
        age=session_info['age'],
        gender=session_info['gender'],
        hair_length=session_info['hair_length'],
        upper_body_length=session_info['upper_body_length'],
        upper_body_color=session_info['upper_body_color'],
        lower_body_length=session_info['lower_body_length'],
        lower_body_color=session_info['lower_body_color'],
        lower_body_type=session_info['lower_body_type'],
        backpack=session_info['backpack'].replace("Yes", "1").replace("No", "0"),
        bag=session_info['bag'].replace("Yes", "1").replace("No", "0"),
        glasses=session_info['glasses'],
        hat=session_info['hat'].replace("Yes", "1").replace("No", "0")
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
