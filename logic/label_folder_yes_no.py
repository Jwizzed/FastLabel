from flask import Blueprint, jsonify, render_template, redirect, url_for, request, session
from models import Image, Label, SkippedImage
from sqlalchemy.sql.expression import func
import cv2
import numpy as np
import base64
from app import db

main = Blueprint('main', __name__)


def initialize_label_questions():
    label_questions = [
        ('ethnicity', 'Select the ethnicity:', ['Mongoloid', 'Caucasoid', 'Negriod']),
        ('age', 'Select the age group:', ['Young', 'Adult', 'Old']),
        ('gender', 'Select the gender:', ['Male', 'Female']),
        ('hair_length', 'Select hair length:', ['Short', 'Bald', 'Long']),
        ('upper_body_length', '(ความยาวแขนเสื้อ) Select the upper body cloth length:', ['Short', 'Long', 'None']),
        ('upper_body_color', 'Select the upper body color:', ['Black', 'Blue', 'Brown', 'Green', 'Grey', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow', 'Other']),
        ('upper_body_type', 'Select the upper body type:', ['Tshirt', 'Shirt', 'Polo', 'Tanktop', 'Jacket', 'Dress', 'Blouse']),
        ('lower_body_length', '(ความยาวขากางเกง) Select the lower body cloth length:', ['Short', 'Long']),
        ('lower_body_color', 'Select the lower body color:', ['Black', 'Blue', 'Brown', 'Green', 'Grey', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow', 'Other']),
        ('lower_body_type', 'Select the lower body type:', ['Trousers&Shorts', 'Skirt&Dress']),
        ('footwear', 'Select the type of footwear:', ['Shoes', 'Sandals']),
        ('backpack', 'Does the person have a backpack?', ['Yes', 'No']),
        ('bag', 'Does the person have a bag?', ['Yes', 'No']),
        ('glasses', 'Does the person wear glasses?', ['Normal', 'Sun', 'No']),
        ('hat', 'Does the person wear a hat?', ['Yes', 'No']),
        ('mask', 'Does the person wear a mask?', ['Yes', 'No'])
    ]
    session['questions'] = label_questions
    session['current_question'] = 0


def initialize_filter_questions():
    filter_questions = [
        ('valid', 'Does the image valid?', ['Yes', 'No'])
    ]
    session['filter_questions'] = filter_questions
    session['current_filter_question'] = 0


@main.route('/')
def index():
    return redirect(url_for('main.label_images'))


@main.route('/label', methods=['GET', 'POST'])
def label_images():
    # print(session)
    if 'label_image_id' in session and 'questions' in session:
        # print("Old session")
        image_id = session['label_image_id']
        image = Image.query.get(image_id)
        image.is_appear_label = True
        db.session.commit()
    else:
        image = (
            Image.query
            .filter_by(is_filter=True)
            .filter_by(is_label=False)
            .filter_by(is_appear_label=False)
            .order_by(func.random())
            .first()
        )
        # print(image)
        if image:
            session['label_image_id'] = image.id
            image.is_appear_label = True
            db.session.commit()
            initialize_label_questions()
    if not image:
        session.pop('label_image_id', None)
        filtered_images = Image.query.filter_by(is_filter=True).count()
        labeled_images = Image.query.filter_by(is_label=True).count()
        total_images = Image.query.count()
        return render_template('unlabeled.html',filtered_images=filtered_images, labeled_images=labeled_images, total_images=total_images)
    
    if request.method == 'POST':
        response = process_label_form(request, image)
        if response:
            return response

    return render_label_current_image(image)

@main.route('/filter', methods=['GET', 'POST'])
def filter_images():
    # print(session)
    if 'filter_image_id' in session and 'filter_questions' in session:
        # print("Filter old session image")
        image_id = session['filter_image_id']
        image = Image.query.get(image_id)
        # print("set is_appear_filter = True")
        image.is_appear_filter = True
        db.session.commit()
    else:
        # print("Get new filter image")
        image = (
            Image.query
            .filter_by(is_filter=False)
            .filter_by(is_appear_filter=False)
            .order_by(func.random())
            .first()
        )
        if image:
            # print("set is_appear_filter = True")
            session['filter_image_id'] = image.id
            image.is_appear_filter = True
            db.session.commit()
            initialize_filter_questions()
    if not image:
        # print("not image")
        session.pop('filter_image_id', None)
        filtered_images = Image.query.filter_by(is_filter=True).count()
        labeled_images = Image.query.filter_by(is_label=True).count()
        total_images = Image.query.count()
        return render_template('unlabeled.html',filtered_images=filtered_images, labeled_images=labeled_images, total_images=total_images)

    if request.method == 'POST':
        response = process_filter_form(request, image)
        if response:
            return response

    return render_filter_current_image(image)

@main.route('/exit_filter', methods=['POST'])
def exit_filter():
    # print("Received exit_filter request")
    try:        
        # Handle filter_image_id session key
        if 'filter_image_id' in session:
            filter_image_id = session['filter_image_id']
            filter_image = Image.query.get(filter_image_id)
            if filter_image:
                # print(filter_image)
                filter_image.is_appear_filter = False
                db.session.commit()
                session.pop('filter_image_id', None)
        
        # Handle label_image_id session key
        if 'label_image_id' in session:
            label_image_id = session['label_image_id']
            label_image = Image.query.get(label_image_id)
            if label_image:
                # print(label_image)
                label_image.is_appear_label = False
                db.session.commit()
                session.pop('label_image_id', None)
        
        # Check if any of the operations were successful
        if 'filter_image_id' not in session and 'label_image_id' not in session:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Some images were not processed'}), 400

    except Exception as e:
        # print(f"Exception: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



def render_filter_current_image(image):
    image_data = cv2.imdecode(np.frombuffer(image.image_data, np.uint8), cv2.IMREAD_COLOR)
    annotated_image = image_data.copy()
    annotated_image = resize_image(annotated_image, 800, 400)
    question, choices = get_filter_questions()
    encoded_image = base64.b64encode(cv2.imencode('.jpg', annotated_image)[1]).decode('utf-8')
    filtered_images = Image.query.filter_by(is_filter=True).count()
    labeled_images = Image.query.filter_by(is_label=True).count()
    total_images = Image.query.count()
    return render_template('filter.html', filtered_images=filtered_images, labeled_images=labeled_images, total_images=total_images, image=encoded_image, question=question, choices=choices)

def render_label_current_image(image):
    image_data = cv2.imdecode(np.frombuffer(image.image_data, np.uint8), cv2.IMREAD_COLOR)
    annotated_image = image_data.copy()
    annotated_image = resize_image(annotated_image, 800, 400)
    question, choices = get_label_questions()
    encoded_image = base64.b64encode(cv2.imencode('.jpg', annotated_image)[1]).decode('utf-8')
    filtered_images = Image.query.filter_by(is_filter=True).count()
    labeled_images = Image.query.filter_by(is_label=True).count()
    total_images = Image.query.count()
    return render_template('label.html', filtered_images=filtered_images, labeled_images=labeled_images, total_images=total_images, image=encoded_image, question=question, choices=choices)

def get_label_questions():
    if 'current_question' in session:
        question_index = session['current_question']
        questions = session['questions']
        if question_index < len(questions):
            attr, question, choices = questions[question_index]
            return question, choices
    return None, []

def get_filter_questions():
    if 'current_filter_question' in session:
        question_index = session['current_filter_question']
        questions = session['filter_questions']
        if question_index < len(questions):
            attr, question, choices = questions[question_index]
            return question, choices
    return None, []


def process_filter_form(request, image):    
    if 'No' in request.form.get('choice'):
        image_instance = Image.query.get(image.id)
        if image_instance:
            db.session.delete(image_instance)
            db.session.commit()
    else:
        image.is_filter = True
        image.is_appear_filter = False
        db.session.commit()
    session.pop('filter_image_id', None)
    return redirect(url_for('main.filter_images'))



def process_label_form(request, image):
    if 'back' in request.form and session['current_question'] > 0:
        session['current_question'] -= 1

    choice = request.form.get('choice')
    if choice:
        attr, _, _ = session['questions'][session['current_question']]
        session[attr] = choice
        session['current_question'] += 1

        if session['current_question'] >= len(session['questions']):
            save_labels_to_db(image, session)
            session.pop('label_image_id', None)

            return redirect(url_for('main.label_images'))

def save_labels_to_db(image, session_info):
    label = Label(
        image_id=image.id,
        ethnicity=session_info['ethnicity'],
        age=session_info['age'],
        gender=session_info['gender'],
        hair_length=session_info['hair_length'],
        upper_body_length=session_info['upper_body_length'],
        upper_body_color=session_info['upper_body_color'],
        upper_body_type=session_info['upper_body_type'],
        lower_body_length=session_info['lower_body_length'],
        lower_body_color=session_info['lower_body_color'],
        lower_body_type=session_info['lower_body_type'],
        footwear=session_info['footwear'],
        backpack=session_info['backpack'].replace("Yes", "1").replace("No", "0"),
        bag=session_info['bag'].replace("Yes", "1").replace("No", "0"),
        glasses=session_info['glasses'],
        hat=session_info['hat'].replace("Yes", "1").replace("No", "0"),
        mask=session_info['mask'].replace("Yes", "1").replace("No", "0"),
    )
    db.session.add(label)
    image.is_label = True
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


