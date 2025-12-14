# penambahan session yang digunakan untuk menyimpan status login pengguna
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sqlite3

app = Flask(__name__)
# kunci rahasia untuk mengenkripsi data session dan berfungsi mengaktifkan mekanisme session Flask.
app.secret_key = "secret-key-sederhana"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///students.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)


# model User ditambahkan sebagai tempat penyimpanan akun untuk proses login.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


# endpoint login digunakan untuk autentikasi dan menyimpan user ke session, logout menghapus session.
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user"] = username
            return redirect(url_for("index"))
        return "Login gagal", 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# pengguna yang belum login tidak bisa mengakses halaman utama dan akan diarahkan ke login.
@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    students = db.session.execute(text("SELECT * FROM student")).fetchall()
    return render_template("index.html", students=students)


# operasi CRUD, dibatasi hanya untuk admin dan pengguna yang sudah login.
@app.route("/add", methods=["POST"])
def add_student():
    if "user" not in session or session["user"] != "admin":
        return redirect(url_for("login"))

    name = request.form["name"]
    age = request.form["age"]
    grade = request.form["grade"]

    connection = sqlite3.connect("instance/students.db")
    cursor = connection.cursor()
    # query = (
    #     f"INSERT INTO student (name, age, grade) VALUES ('{name}', {age}, '{grade}')"
    # )
    # cursor.execute(query)
    db.session.execute(
    text("INSERT INTO student (name, age, grade) VALUES (:name, :age, :grade)"),
    {"name": name, "age": age, "grade": grade}
        )
    db.session.commit()
    connection.commit()
    connection.close()

    return redirect(url_for("index"))


@app.route("/delete/<string:id>")
def delete_student(id):
    if "user" not in session or session["user"] != "admin":
        return redirect(url_for("login"))

    db.session.execute(text(f"DELETE FROM student WHERE id={id}"))
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if "user" not in session or session["user"] != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        grade = request.form["grade"]

        db.session.execute(
            text(
                f"UPDATE student SET name='{name}', age={age}, grade='{grade}' WHERE id={id}"
            )
        )
        db.session.commit()
        return redirect(url_for("index"))

    student = db.session.execute(
        text(f"SELECT * FROM student WHERE id={id}")
    ).fetchone()
    return render_template("edit.html", student=student)


# pembuatan akun default memudahkan pengujian fitur login & otorisasi.
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Seed accounts
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", password="admin")
            db.session.add(admin_user)
        if not User.query.filter_by(username="user").first():
            user_user = User(username="user", password="user")
            db.session.add(user_user)
        db.session.commit()
    app.run(host="0.0.0.0", port=5000, debug=True)
