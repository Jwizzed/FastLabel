from flask import Blueprint, jsonify, render_template, redirect, url_for, request, session
from sqlalchemy import or_
from models import Image, IsUseGroupId
from sqlalchemy.sql.expression import func
import cv2
import numpy as np
import base64
from app import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.filter_images'))

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

# filter section
def getImageFromGroupId(group_id):
    image = Image.query.filter_by(group_id=group_id, is_filter=False, is_appear_filter=False).first()
    if not image :
        return None
    image.is_appear_filter = True
    db.session.commit()
    return image

def initialize_filter_questions():
    question = 'Is the image valid?'
    choices = ['Yes', 'No']
    return question, choices

@main.route('/filter', methods=['GET', 'POST'])
def filter_images():
    if not "filter_image_id" in session :
        # Get group id that not appeared
        if 'filter_group_id' not in session:
            # print("Get new group id")
            image = (
                Image.query
                .join(IsUseGroupId, (Image.group_id == IsUseGroupId.group_id) & (IsUseGroupId.is_appear == False))
                .filter(Image.is_filter == False, Image.is_appear_filter == False)
                .order_by(func.random())
                .first()
            )
            if image:
                group_id = image.group_id
                session['filter_group_id'] = group_id
                # print(session)
                # print("update group id to true")
                db.session.query(IsUseGroupId).filter_by(group_id=group_id).update({'is_appear': True})
                db.session.commit()
            else:
                filtered_images = Image.query.filter_by(is_filter=True).count()
                total_images = Image.query.count()
                return render_template('unlabeled.html',filtered_images=filtered_images, total_images=total_images)
        else:
            # print("Old group id")
            group_id = session['filter_group_id']


        # Get image from that group id
        image = getImageFromGroupId(group_id)
        # print(image)
        if not image : 
            # print(f"group : {group_id} finish")
            group = IsUseGroupId.query.get(group_id)
            group.is_all_filter = True
            agent_img = Image.query.filter_by(group_id=group_id, is_filter=True).order_by(func.random()).first()
            if agent_img :
                group.agent_image_id = agent_img.id
                db.session.commit()
            session.pop('filter_group_id', None)
            return redirect(url_for('main.filter_images'))
        session['filter_image_id'] = image.id
        # print(session)
    
    else :
        image_id = session['filter_image_id']
        image = Image.query.get(image_id)
        image.is_appear_filter = True
        db.session.commit()
        if request.method == 'POST':
            response = process_filter_form(request, image)
            if response:
                return response
    
    return render_filter_current_image(image)

def render_filter_current_image(image):
    image_data = cv2.imdecode(np.frombuffer(image.image_data, np.uint8), cv2.IMREAD_COLOR)
    annotated_image = image_data.copy()
    annotated_image = resize_image(annotated_image, 800, 400)
    question, choices = initialize_filter_questions()
    encoded_image = base64.b64encode(cv2.imencode('.jpg', annotated_image)[1]).decode('utf-8')
    filtered_images_num = Image.query.filter_by(is_filter=True).count()
    label_images_num = IsUseGroupId.query.filter_by(is_all_filter=True).count()
    total_images_num = Image.query.count()
    return render_template('filter.html', filtered_images_num=filtered_images_num, label_images_num=label_images_num, total_images_num=total_images_num, image=encoded_image, question=question, choices=choices)

def process_filter_form(request, image):    
    if 'No' in request.form.get('choice'):
        image_instance = Image.query.get(image.id)
        if image_instance:
            db.session.delete(image_instance)
            db.session.commit()
    elif 'Yes' in request.form.get('choice'):
        image.is_filter = True
        db.session.commit()
    session.pop('filter_image_id', None)
    return redirect(url_for('main.filter_images'))


# label section
def initialize_label_questions():
    return [
        ('ethnicity', 'Select the ethnicity:', ['Mongoloid', 'Caucasoid', 'Negroid']),
        ('age', 'Select the age group:', ['Young', 'Adult', 'Old']),
        ('gender', 'Select the gender:', ['Male', 'Female']),
        ('hair_length', 'Select hair length:', ['Short', 'Bald', 'Long']),
        ('upper_body_length', '(ความยาวแขนเสื้อ) Select the upper body cloth length:', ['Short', 'Long', 'None']),
        ('upper_body_color', 'Select the upper body color:', ['Black', 'Blue', 'Brown', 'Green', 'Grey', 'Orange', 'Pink', 'Purple', 'Red', 'White', 'Yellow', 'Other', 'None']),
        ('upper_body_type', 'Select the upper body type:', ['Tshirt', 'Shirt', 'Polo', 'Tanktop', 'Jacket', 'Dress', 'Blouse', 'None']),
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

def check_each_label_status_num(all_label_images_num) :
    questions = initialize_label_questions()
    label_nums = []
    for question in questions :
        non_label_num = (
            Image.query
            .join(IsUseGroupId, Image.id == IsUseGroupId.agent_image_id)
            .filter(or_(getattr(Image, question[0]) == None, getattr(Image, question[0]) == "false"))
            .count()
        )
        label_num = all_label_images_num - non_label_num
        label_nums.append(label_num)
    return label_nums

@main.route('/label')
def label_images():
    label_image_id = session.get("label_image_id")
    label_question = session.get("label_question")
    if label_question and label_image_id :
        image = Image.query.get(label_image_id)
        setattr(image, label_question, None)
        db.session.commit()
        session.pop("label_question", None)
        session.pop("label_image_id", None)
    questions = initialize_label_questions()
    filtered_images_num = Image.query.filter_by(is_filter=True).count()
    total_images_num = Image.query.count()
    all_label_images_num = IsUseGroupId.query.filter(IsUseGroupId.agent_image_id != None).count()
    labeled_images_num = check_each_label_status_num(all_label_images_num)
    return render_template('label.html', questions=questions, filtered_images_num=filtered_images_num, total_images_num=total_images_num, labeled_images_num=labeled_images_num, all_label_images_num=all_label_images_num)



@main.route('/question/<question_id>', methods=['GET', 'POST'])
def question_page(question_id):
    session["label_question"] = question_id
    # Get image
    if not "label_image_id" in session :
        # Get New Image
        image = (
            Image.query
            .join(IsUseGroupId, IsUseGroupId.agent_image_id == Image.id)
            .filter(IsUseGroupId.agent_image_id != None)
            .filter(getattr(Image, question_id) == None)
            .order_by(func.random())
            .first()
        )
        if image:
            session['label_image_id'] = image.id
            image = Image.query.get(image.id)
            setattr(image, question_id, False)
            db.session.commit()
        else:
            filtered_images = Image.query.filter_by(is_filter=True).count()
            total_images = Image.query.count()
            return render_template('unlabeled.html',filtered_images=filtered_images, total_images=total_images)
    else :
        image_id = session['label_image_id']
        image = Image.query.get(image_id)
        setattr(image, question_id, False)
        db.session.commit()
        if request.method == 'POST':
            response = process_label_form(request, question_id, image)
            if response:
                return response
    
    questions = initialize_label_questions()
    question = next((q for q in questions if q[0] == question_id), None)
    if question:
        return render_label_current_image(image, question)
    return redirect(url_for('main.label_images'))

def render_label_current_image(image, question):
    image_data = cv2.imdecode(np.frombuffer(image.image_data, np.uint8), cv2.IMREAD_COLOR)
    annotated_image = image_data.copy()
    annotated_image = resize_image(annotated_image, 800, 400)
    encoded_image = base64.b64encode(cv2.imencode('.jpg', annotated_image)[1]).decode('utf-8')
    non_label_num = (
        Image.query
        .join(IsUseGroupId, Image.id == IsUseGroupId.agent_image_id)
        .filter(or_(getattr(Image, question[0]) == None, getattr(Image, question[0]) == "false"))
        .count()
    ) 
    all_label_images_num = IsUseGroupId.query.filter(IsUseGroupId.agent_image_id != None).count()
    filtered_images_num = Image.query.filter_by(is_filter=True).count()
    total_images_num = Image.query.count()
    return render_template('question.html', filtered_images_num=filtered_images_num, total_images_num=total_images_num, labeled_images=all_label_images_num-non_label_num, need_label_images=all_label_images_num, image=encoded_image, question=question)

def process_label_form(request, question_id, image):    
    option = request.form.get('choice')
    if option:
        group_id = image.group_id
        images_to_update = Image.query.filter_by(group_id=group_id).all()
        for img in images_to_update:
            setattr(img, question_id, option)
        db.session.commit()
        session.pop("label_image_id", None)
        session.pop("label_question", None)
    else:
        print("No option selected")
    return redirect(url_for('main.question_page', question_id=question_id))



@main.route('/exit_filter', methods=['POST'])
def exit_filter():
    # print(session)
    # print("Received exit_filter request")
    try:        
        # Handle filter_image_id session key
        if 'filter_image_id' in session:
            filter_image_id = session['filter_image_id']
            filter_image = Image.query.get(filter_image_id)
            if filter_image:
                # print(filter_image)
                filter_image.is_appear_filter = False
                group_id = filter_image.group_id
                group = IsUseGroupId.query.get(group_id)
                group.is_appear = False
                db.session.commit()
                session.pop('filter_image_id', None)
        
        # Handle label_image_id session key
        if 'label_image_id' in session:
            label_image_id = session['label_image_id']
            image = Image.query.get(label_image_id)
            question_id = session.get("label_question")
            if image:
                # print(label_image)
                setattr(image, question_id, None)
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


