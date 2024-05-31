from flask import Blueprint, render_template, redirect, url_for, request, session
from models import Image
from sqlalchemy.sql.expression import func
import cv2
import numpy as np
import base64
from app import db

main = Blueprint('main', __name__)


def initialize_label_questions():
    questions = [
        ('valid', 'Does the image valid?', ['Yes', 'No'])
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


def get_label_questions():
    if 'current_question' in session:
        question_index = session['current_question']
        questions = session['questions']
        if question_index < len(questions):
            attr, question, choices = questions[question_index]
            return question, choices
    return None, []


def process_label_form(request, image):
    if 'No' in request.form.get('choice'):
        image_instance = Image.query.get(image.id)
        if image_instance:
            db.session.delete(image_instance)
            db.session.commit()
    session.clear()
    return redirect(url_for('main.label_images'))


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
