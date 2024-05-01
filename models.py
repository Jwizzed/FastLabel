from app import db

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folder = db.Column(db.String(100))
    image_name = db.Column(db.String(100))
    image_data = db.Column(db.LargeBinary)

class Label(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    upper_label = db.Column(db.String(100))
    lower_label = db.Column(db.String(100))
    shoe_label = db.Column(db.String(100))
    upper_label_x = db.Column(db.Integer)
    upper_label_y = db.Column(db.Integer)
    upper_label_width = db.Column(db.Integer)
    upper_label_height = db.Column(db.Integer)
    lower_label_x = db.Column(db.Integer)
    lower_label_y = db.Column(db.Integer)
    lower_label_width = db.Column(db.Integer)
    lower_label_height = db.Column(db.Integer)

class SkippedImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))