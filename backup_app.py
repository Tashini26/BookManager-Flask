import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# PostgreSQL database URL — replace with your own credentials
DATABASE_URL = 'postgresql://postgres:T2002@localhost:5432/bookdb'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database setup
db = SQLAlchemy(app)

# Book model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    genre = db.Column(db.String(100), nullable=True)

# Form for Add/Edit
class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    author = StringField('Author', validators=[DataRequired(), Length(max=150)])
    year = IntegerField('Year', validators=[Optional(), NumberRange(min=0, max=9999)])
    genre = StringField('Genre', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Save')

# Routes
@app.route('/')
def index():
    books = Book.query.order_by(Book.id.asc()).all()
    return render_template('index.html', books=books)

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    form = BookForm()
    if form.validate_on_submit():
        book = Book(
            title=form.title.data.strip(),
            author=form.author.data.strip(),
            year=form.year.data,
            genre=form.genre.data.strip() if form.genre.data else None
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('add_edit.html', form=form, action='Add')

@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)
    if form.validate_on_submit():
        book.title = form.title.data.strip()
        book.author = form.author.data.strip()
        book.year = form.year.data
        book.genre = form.genre.data.strip() if form.genre.data else None
        db.session.commit()
        flash('Book updated successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('add_edit.html', form=form, action='Edit')

@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully.', 'success')
    return redirect(url_for('index'))

# Seed sample books on first request

def seed_data():
   with app.app_context():
    db.create_all()
    if Book.query.count() == 0:
        sample_books = [
            Book(title='To Kill a Mockingbird', author='Harper Lee', year=1960, genre='Fiction'),
            Book(title='1984', author='George Orwell', year=1949, genre='Dystopian'),
            Book(title='The Great Gatsby', author='F. Scott Fitzgerald', year=1925, genre='Classic'),
            Book(title='Pride and Prejudice', author='Jane Austen', year=1813, genre='Romance'),
            Book(title='The Hobbit', author='J.R.R. Tolkien', year=1937, genre='Fantasy')
        ]
        db.session.bulk_save_objects(sample_books)
        db.session.commit()

# Call seed_data() when app starts
seed_data() 

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
