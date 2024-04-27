from flask import Flask, render_template, redirect, url_for, request, session
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from flask_uploads import UploadSet, configure_uploads, IMAGES
import cv2
import pandas as pd
import os
import base64


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOADED_IMAGES_DEST'] = 'uploads'

images = UploadSet('images', IMAGES)
configure_uploads(app, images)


class LabelingForm(FlaskForm):
    upper_label = SelectField('Upper Cloth', choices=[
        ('Polo', 'Polo'),
        ('Long sleeve T-shirt', 'Long sleeve T-shirt'),
        ('Long sleeve shirt', 'Long sleeve shirt'),
        ('Short sleeve Shirt', 'Short sleeve Shirt'),
        ('Short sleeve T-shirt', 'Short sleeve T-shirt'),
        ('Sleeveless', 'Sleeveless'),
        ('Long sleeve blouse', 'Long sleeve blouse'),
        ('Short sleeve blouse', 'Short sleeve blouse'),
        ('Dress', 'Dress'),
        ('Outwear', 'Outwear')
    ])
    lower_label = SelectField('Lower Cloth', choices=[
        ('Trousers', 'Trousers'),
        ('Shorts', 'Shorts'),
        ('Skirt', 'Skirt')
    ])
    shoe_label = SelectField('Shoes', choices=[
        ('Sandals', 'Sandals'),
        ('Sneakers', 'Sneakers'),
        ('High heels', 'High heels'),
        ('Leather shoes', 'Leather shoes'),
        ('None', 'None')
    ])
    skip = SubmitField('Skip')
    submit = SubmitField('Submit')


@app.route('/')
def index():
    folders = ['folder1', 'folder2', 'folder3', 'folder4', 'folder5']
    return render_template('index.html', folders=folders)


@app.route('/label/<folder>', methods=['GET', 'POST'])
def label_folder(folder):
    image_extensions = ['.jpeg', '.jpg', '.png']
    image_files = [f for f in os.listdir(f'uploads/{folder}') if os.path.splitext(f)[1].lower() in image_extensions]
    labeled_images = set()
    skipped_images = set()

    if os.path.exists(f'uploads/{folder}/labels.csv'):
        df = pd.read_csv(f'uploads/{folder}/labels.csv')
        labeled_images = set(df['image_name'])

    if os.path.exists(f'uploads/{folder}/skipped.csv'):
        df_skipped = pd.read_csv(f'uploads/{folder}/skipped.csv')
        skipped_images = set(df_skipped['image_name'])

    unlabeled_images = [img for img in image_files if img not in labeled_images and img not in skipped_images]

    if not unlabeled_images:
        return render_template('unlabeled.html')

    image_name = unlabeled_images[0]
    image_path = f'uploads/{folder}/{image_name}'
    annotation_path = f'uploads/{folder}/{os.path.splitext(image_name)[0]}.txt'

    annotated_image = cv2.imread(image_path)
    original_height, original_width = annotated_image.shape[:2]

    with open(annotation_path, 'r') as f:
        annotations = f.readlines()

    upper_label_xy = None
    lower_label_xy = None

    for annotation in annotations:
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

    if upper_label_xy is not None:
        x1, y1, x2, y2 = upper_label_xy
        x1_resized = int(x1 * resized_width / original_width)
        y1_resized = int(y1 * resized_height / original_height)
        x2_resized = int(x2 * resized_width / original_width)
        y2_resized = int(y2 * resized_height / original_height)
        cv2.rectangle(annotated_image, (x1_resized, y1_resized), (x2_resized, y2_resized), (0, 255, 0), 2)

    if lower_label_xy is not None:
        x1, y1, x2, y2 = lower_label_xy
        x1_resized = int(x1 * resized_width / original_width)
        y1_resized = int(y1 * resized_height / original_height)
        x2_resized = int(x2 * resized_width / original_width)
        y2_resized = int(y2 * resized_height / original_height)
        cv2.rectangle(annotated_image, (x1_resized, y1_resized), (x2_resized, y2_resized), (0, 255, 0), 2)

    _, file_extension = os.path.splitext(image_name)
    file_extension = file_extension.lower()

    if file_extension == '.png':
        retval, buffer = cv2.imencode('.png', annotated_image)
    else:
        retval, buffer = cv2.imencode('.jpg', annotated_image)

    if not retval:
        return "Error encoding the image."

    image_base64 = base64.b64encode(buffer).decode('utf-8')

    if request.method == 'POST':
        if 'skip' in request.form:
            data = {'image_name': image_name}
            df_skipped = pd.DataFrame([data])
            df_skipped.to_csv(f'uploads/{folder}/skipped.csv', mode='a', header=not os.path.exists(f'uploads/{folder}/skipped.csv'), index=False)
            session.clear()
            return redirect(url_for('label_folder', folder=folder))

        choice = request.form['choice']
        if 'upper_label' not in session:
            session['upper_label'] = choice
            question = 'Select the lower cloth:'
            choices = ['Trousers', 'Shorts', 'Skirt']
        elif 'lower_label' not in session:
            session['lower_label'] = choice
            question = 'Select the shoes:'
            choices = ['Sandals', 'Sneakers', 'High heels', 'Leather shoes', 'None']
        else:
            session['shoe_label'] = choice
            data = {
                'image_name': image_name,
                'upper_label': session['upper_label'],
                'lower_label': session['lower_label'],
                'shoe_label': session['shoe_label'],
                'upper_label_x': upper_label_xy[0] if upper_label_xy else '',
                'upper_label_y': upper_label_xy[1] if upper_label_xy else '',
                'upper_label_width': upper_label_xy[2] - upper_label_xy[0] if upper_label_xy else '',
                'upper_label_height': upper_label_xy[3] - upper_label_xy[1] if upper_label_xy else '',
                'lower_label_x': lower_label_xy[0] if lower_label_xy else '',
                'lower_label_y': lower_label_xy[1] if lower_label_xy else '',
                'lower_label_width': lower_label_xy[2] - lower_label_xy[0] if lower_label_xy else '',
                'lower_label_height': lower_label_xy[3] - lower_label_xy[1] if lower_label_xy else ''
            }
            df = pd.DataFrame([data])
            df.to_csv(f'uploads/{folder}/labels.csv', mode='a', header=not os.path.exists(f'uploads/{folder}/labels.csv'), index=False)
            session.clear()
            return redirect(url_for('label_folder', folder=folder))
    else:
        session.clear()
        question = 'Select the upper cloth:'
        choices = ['Polo', 'Long sleeve T-shirt', 'Long sleeve shirt', 'Short sleeve Shirt', 'Short sleeve T-shirt',
                   'Sleeveless', 'Long sleeve blouse', 'Short sleeve blouse', 'Dress', 'Outwear']

    return render_template('label.html', image=image_base64, question=question, choices=choices)


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
