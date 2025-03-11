from flask_sqlalchemy import SQLAlchemy

DATABASE_URL = "mysql+pymysql://root:root@localhost:3307/HistorialPartidos"


db = SQLAlchemy()

def init_app(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
