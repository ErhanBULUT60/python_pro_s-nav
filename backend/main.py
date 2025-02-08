from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, ExamScore, Question
import random
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db.init_app(app)
migrate = Migrate(app, db)

def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/')
def home():
    highest_score = db.session.query(db.func.max(User.highest_score)).scalar() or 0
    global_highest_score = db.session.query(db.func.max(ExamScore.score)).scalar() or 0
    return render_template('exam.html', highest_score=highest_score, global_highest_score=global_highest_score)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # Check if the email already exists
        if User.query.filter_by(email=email).first():
            flash('Bu email zaten kullanılıyor!', 'danger')
            return redirect(url_for('register'))  
        hashed_password = generate_password_hash(password)  
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Giriş başarılı!', 'success')
            return redirect(url_for('exam'))
        else:
            flash('Kullanıcı adı veya şifre yanlış.', 'danger')
    return render_template('login.html')

@app.route('/exam', methods=['GET', 'POST'])
def exam():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        score = 0
        answers = {q.id: q.correct_answer for q in Question.query.all()}
        for key, value in answers.items():
            if request.form.get(str(key)) == value:
                score += 1
        # Puanı 100 üzerinden hesaplayın
        total_score = (score / 5) * 100
        user = User.query.get(session['user_id'])
        new_score = ExamScore(user_id=user.id, score=total_score)
        db.session.add(new_score)
        if total_score > user.highest_score:
            user.highest_score = total_score
        db.session.commit()
        highest_score = db.session.query(db.func.max(User.highest_score)).scalar() or 0
        global_highest_score = db.session.query(db.func.max(ExamScore.score)).scalar() or 0
        return render_template('result.html', score=total_score, highest_score=user.highest_score, global_highest_score=global_highest_score)
    else:
        questions = Question.query.all()
        if len(questions) >= 5:
            questions = random.sample(questions, 5)
        highest_score = db.session.query(db.func.max(User.highest_score)).scalar() or 0
        global_highest_score = db.session.query(db.func.max(ExamScore.score)).scalar() or 0
        return render_template('exam.html', questions=questions, highest_score=highest_score, global_highest_score=global_highest_score)

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True)