from app import db


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(100))
    image_data = db.Column(db.LargeBinary)
    is_appear_filter = db.Column(db.Boolean, default=False)
    is_appear_label = db.Column(db.Boolean, default=False)
    is_filter = db.Column(db.Boolean, default=False)
    is_label = db.Column(db.Boolean, default=False)



class Label(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))

    ethnicity = db.Column(db.String(100))
    age = db.Column(db.String(100))
    gender = db.Column(db.String(100))
    hair_length = db.Column(db.String(100))
    upper_body_length = db.Column(db.String(100))
    upper_body_color = db.Column(db.String(100))
    upper_body_type = db.Column(db.String(100))
    lower_body_length = db.Column(db.String(100))
    lower_body_color = db.Column(db.String(100))
    lower_body_type = db.Column(db.String(100))
    footwear = db.Column(db.String(100))
    backpack = db.Column(db.String(1))
    bag = db.Column(db.String(1))
    glasses = db.Column(db.String(100))
    hat = db.Column(db.String(1))
    mask = db.Column(db.String(1))


class SkippedImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    image = db.relationship('Image', backref=db.backref('skipped', lazy=True))
