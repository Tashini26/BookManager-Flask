import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# PostgreSQL database URL — using your password T2002
DATABASE_URL = 'postgresql://postgres:T2002@localhost:5432/bookdb'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database setup
db = SQLAlchemy(app)

# Book model
from datetime import datetime

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String(100))  # ✅ Add this line
    price = db.Column(db.Float, nullable=False)

# Bill model
class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=db.func.now())


    # ✅ This is the ONLY relationship, and it is correct
    book = db.relationship('Book', backref='bills')



# Form for Add/Edit
class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    author = StringField('Author', validators=[DataRequired(), Length(max=150)])
    year = IntegerField('Year', validators=[Optional(), NumberRange(min=0, max=9999)])
    price = IntegerField('Price', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Save')


# Index route with search and sort
@app.route('/')
def index():
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'id')

    query = Book.query

    if search:
        query = query.filter(
            (Book.title.ilike(f'%{search}%')) |
            (Book.author.ilike(f'%{search}%'))
        )

    if sort_by == 'title':
        query = query.order_by(Book.title.asc())
    elif sort_by == 'year':
        query = query.order_by(Book.year.asc())
    else:
        query = query.order_by(Book.id.asc())

    books = query.all()
    return render_template('index.html', books=books, search=search, sort_by=sort_by)

# Add book
@app.route('/add', methods=['GET', 'POST'])
def add_book():
    form = BookForm()
    if form.validate_on_submit():
        book = Book(
    title=form.title.data.strip(),
    author=form.author.data.strip(),
    year=form.year.data,
    price=form.price.data
)

        try:
            db.session.add(book)
            db.session.commit()
            flash('Book added successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {e}', 'error')
        return redirect(url_for('index'))
    return render_template('add_edit.html', form=form, action='Add')

@app.route('/billing', methods=['GET', 'POST'])
def billing():
    books = Book.query.all()
    selected_book_id = request.args.get('book_id', type=int)

    if request.method == 'POST':
        selected_book_id = request.form.get('book_id', type=int)
        quantity = request.form.get('quantity', type=int)
        book = Book.query.get(selected_book_id)
        total_price = quantity * book.price

        bill = Bill(book_id=selected_book_id, quantity=quantity, total_price=total_price)
        db.session.add(bill)
        db.session.commit()

      
        return render_template('billing.html', books=books, message="Bill saved successfullyyy!")
       

    return render_template('billing.html', books=books, selected_book_id=selected_book_id)


@app.route('/bills')
def bill_history():
    bills = Bill.query.order_by(Bill.created_at.desc()).all()
    return render_template('bill_history.html', bills=bills)

@app.route('/bills/delete/<int:bill_id>', methods=['POST'])
def delete_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    db.session.delete(bill)
    db.session.commit()
    flash('Bill deleted successfully!', 'success')
    return redirect(url_for('bill_history'))



# Edit book
@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)
    if form.validate_on_submit():
        book.title = form.title.data.strip()
        book.author = form.author.data.strip()
        book.year = form.year.data
        book.price = form.price.data 

        try:
            db.session.commit()
            flash('Book updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating book: {e}', 'error')
        return redirect(url_for('index'))
    return render_template('add_edit.html', form=form, action='Edit')

# Delete book
@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    try:
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting book: {e}', 'error')
    return redirect(url_for('index'))

    

# Seed sample data safely
# Seed sample data safely
def seed_data():
    try:
        with app.app_context():
            db.create_all()
            if Book.query.count() == 0:
                sample_books = [
                    Book(title='To Kill a Mockingbird', author='Harper Lee', year=1960, price=1200.00),
                    Book(title='1984', author='George Orwell', year=1949,  price=1500.00),
                    Book(title='The Great Gatsby', author='F. Scott Fitzgerald', year=1925, price=1100.00),
                    Book(title='Pride and Prejudice', author='Jane Austen', year=1813, price=900.00),
                    Book(title='The Hobbit', author='J.R.R. Tolkien', year=1937, price=1800.00)
                ]
                db.session.bulk_save_objects(sample_books)
                db.session.commit()
        print("✅ Database seeded successfully with sample books!")
    except Exception as e:
        print("❌ Error seeding database:", e)


# Call seed_data safely
seed_data()

# Run the app
if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)
