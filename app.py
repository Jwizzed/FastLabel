from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://fastlabel_db_user:oRezOaGhcqT6BPWB6NBiyXxOPdo5URUN@dpg-cp0p5h021fec7388h4ig-a.singapore-postgres.render.com/fastlabel_db"#os.environ.get('DATABASE_URL', 'sqlite:///data.db')

db = SQLAlchemy(app)

from logic.label_folder_yes_no import main
app.register_blueprint(main)

if __name__ == '__main__':
     app.run() 
