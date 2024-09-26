from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
db = SQLAlchemy(app)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(2000), nullable=False)
    correct_answer = db.Column(db.String(1000), nullable=False)
    options = db.relationship('Option', backref='question', lazy=True)

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1000), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

# Predefined questions and answers
quiz_data = [
    {
        "question": "What is the capital of France?",
        "correct_answer": "Paris",
        "options": ["London", "Berlin", "Paris", "Madrid"]
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "correct_answer": "Mars",
        "options": ["Venus", "Mars", "Jupiter", "Saturn"]
    },
    {
        "question": "What is the largest mammal in the world?",
        "correct_answer": "Blue Whale",
        "options": ["African Elephant", "Blue Whale", "Giraffe", "Hippopotamus"]
    },
    {
        "question": "Who painted the Mona Lisa?",
        "correct_answer": "Leonardo da Vinci",
        "options": ["Vincent van Gogh", "Pablo Picasso", "Leonardo da Vinci", "Michelangelo"]
    },
    {
        "question": "What is the chemical symbol for gold?",
        "correct_answer": "Au",
        "options": ["Ag", "Fe", "Au", "Cu"]
    },
    {
        "question": "Which country is home to the kangaroo?",
        "correct_answer": "Australia",
        "options": ["New Zealand", "South Africa", "Australia", "Brazil"]
    },
    {
        "question": "What is the largest organ in the human body?",
        "correct_answer": "Skin",
        "options": ["Liver", "Brain", "Skin", "Heart"]
    },
    {
        "question": "Who wrote 'Romeo and Juliet'?",
        "correct_answer": "William Shakespeare",
        "options": ["Charles Dickens", "Jane Austen", "William Shakespeare", "Mark Twain"]
    },
    {
        "question": "What is the capital of Japan?",
        "correct_answer": "Tokyo",
        "options": ["Beijing", "Seoul", "Bangkok", "Tokyo"]
    },
    {
        "question": "Which element has the chemical symbol 'O'?",
        "correct_answer": "Oxygen",
        "options": ["Gold", "Silver", "Oxygen", "Carbon"]
    },
    {
        "question": "What is the largest planet in our solar system?",
        "correct_answer": "Jupiter",
        "options": ["Saturn", "Jupiter", "Neptune", "Uranus"]
    },
    {
        "question": "Who is known as the father of modern physics?",
        "correct_answer": "Albert Einstein",
        "options": ["Isaac Newton", "Niels Bohr", "Albert Einstein", "Galileo Galilei"]
    },
    {
        "question": "What is the main ingredient in guacamole?",
        "correct_answer": "Avocado",
        "options": ["Tomato", "Onion", "Avocado", "Lime"]
    },
    {
        "question": "Which ocean is the largest?",
        "correct_answer": "Pacific Ocean",
        "options": ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "Pacific Ocean"]
    },
    {
        "question": "What is the capital of Brazil?",
        "correct_answer": "Brasília",
        "options": ["Rio de Janeiro", "São Paulo", "Brasília", "Salvador"]
    }

]

def init_db():
    db.create_all()
    
    # Check if questions already exist
    if Question.query.first() is None:
        for item in quiz_data:
            question = Question(text=item['question'], correct_answer=item['correct_answer'])
            db.session.add(question)
            db.session.flush()  # This assigns an ID to the question

            for option_text in item['options']:
                option = Option(text=option_text, question_id=question.id)
                db.session.add(option)
        
        db.session.commit()

@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('home.html', username=session['username'])
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        flash('Please log in to take the quiz', 'error')
        return redirect(url_for('login'))
    questions = Question.query.all()
    session['quiz_start_time'] = time.time()
    session['quiz_duration'] = 300  # 5 minutes in seconds
    return render_template('quiz.html', questions=questions, quiz_duration=session['quiz_duration'])

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        flash('Please log in to submit the quiz', 'error')
        return redirect(url_for('login'))
    
    score = 0
    questions = Question.query.all()
    for question in questions:
        submitted_answer = request.form.get(f'q{question.id}')
        if submitted_answer == question.correct_answer:
            score += 1
    return render_template('result.html', score=score, total=len(questions))

@app.route('/check_time', methods=['GET'])
def check_time():
    if 'quiz_start_time' not in session or 'quiz_duration' not in session:
        return jsonify({'time_left': 0})
    
    elapsed_time = time.time() - session['quiz_start_time']
    time_left = max(0, session['quiz_duration'] - elapsed_time)
    return jsonify({'time_left': int(time_left)})

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)