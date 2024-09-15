from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class RegisterKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_hash = db.Column(db.String(256), nullable=False)

    def set_register_key(self, key):
        self.key_hash = generate_password_hash(key)

    def check_register_key(self, key):
        return check_password_hash(self.key_hash, key)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer)
    image_name = db.Column(db.String(100))
    image_data = db.Column(db.LargeBinary)
    is_appear_filter = db.Column(db.Boolean, default=False)
    is_filter = db.Column(db.Boolean, default=False)
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
    backpack = db.Column(db.String(100))
    bag = db.Column(db.String(100))
    glasses = db.Column(db.String(100))
    hat = db.Column(db.String(100))
    mask = db.Column(db.String(100))

class IsUseGroupId(db.Model) :
    group_id = db.Column(db.Integer, primary_key=True)
    is_appear = db.Column(db.Boolean, default=False)
    is_all_filter = db.Column(db.Boolean, default=False)
    agent_image_id = db.Column(db.Integer)


class InvalidImage(db.Model) :
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer)
    group_id = db.Column(db.Integer)
    image_name = db.Column(db.String(100))
    image_data = db.Column(db.LargeBinary)


class PredictedResult(db.Model) :
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(100))
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
    backpack = db.Column(db.String(100))
    bag = db.Column(db.String(100))
    glasses = db.Column(db.String(100))
    hat = db.Column(db.String(100))
    mask = db.Column(db.String(100))


class GtData(db.Model) :
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(100))
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
    backpack = db.Column(db.String(100))
    bag = db.Column(db.String(100))
    glasses = db.Column(db.String(100))
    hat = db.Column(db.String(100))
    mask = db.Column(db.String(100))