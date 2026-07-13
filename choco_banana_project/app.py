from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
# ბაზის სახელი და საიდუმლო გასაღები პროექტისთვის
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chocobanana.db'
app.config['SECRET_KEY'] = 'tbc_geolab_secret_key_2026'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- მონაცემთა ბაზის მოდელები  ---

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ფორმები ვალიდაციით  ---

class RegistrationForm(FlaskForm):
    username = StringField('მომხმარებლის სახელი', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('ელ-ფოსტა', validators=[DataRequired(), Email()])
    password = PasswordField('პაროლი', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('გაიმეორეთ პაროლი', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('რეგისტრაცია')

class LoginForm(FlaskForm):
    email = StringField('ელ-ფოსტა', validators=[DataRequired(), Email()])
    password = PasswordField('პაროლი', validators=[DataRequired()])
    submit = SubmitField('შესვლა')

class OrderForm(FlaskForm):
    name = StringField('სახელი, გვარი', validators=[DataRequired()])
    phone = StringField('ტელეფონის ნომერი', validators=[DataRequired()])
    address = StringField('მიტანის მისამართი', validators=[DataRequired()])
    notes = TextAreaField('კომენტარი შეკვეთაზე')
    submit = SubmitField('შეკვეთის დადასტურება')

# --- საიტის გვერდები  ---

@app.route('/')
def home():
    # აქ მინდოდა ბაზიდან წამოღება, მაგრამ ჯერ ჯინჯას ლუპის დასატესტად მასივი გამოვიყენე
    desserts = [
        {"title": "შოკო-ბანანის მაფინი", "desc": "ნატურალური კაკაო, მწიფე ბანანი, შაქრის გარეშე.", "price": "5.00 ₾", "top": True},
        {"title": "ბანანის ბრაუნი", "desc": "შავი შოკოლადითა და ნიგვზით გაჯერებული ჰაეროვანი დესერტი.", "price": "7.50 ₾", "top": False},
        {"title": "პრემიუმ ჩოკო ტორტი", "desc": "სპეციალური შეკვეთით დამზადებული ნატურალური ტორტი.", "price": "25.00 ₾", "top": False}
    ]
    return render_template('index.html', desserts=desserts)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    form = OrderForm()
    if form.validate_on_submit():
        # ფორმიდან მონაცემების შენახვა ბაზაში
        new_order = Order(
            name=form.name.data,
            phone=form.phone.data,
            address=form.address.data,
            notes=form.notes.data
        )
        db.session.add(new_order)
        db.session.commit()
        flash('შეკვეთა წარმატებით გაფორმდა და შეინახა ბაზაში!', 'success')
        return redirect(url_for('home'))
    return render_template('checkout.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # ადმინის პაროლის და ლოგინის შემოწმება
        if form.username.data.lower() == 'admin' and form.password.data == 'sunday15':
            is_admin = True
        else:
            is_admin = False
        
        user = User(username=form.username.data, email=form.email.data, password=form.password.data, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash('რეგისტრაცია წარმატებით გაიარეთ! შეგიძლიათ შეხვიდეთ.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash('წარმატებით შეხვედით სისტემაში!', 'success')
            return redirect(url_for('home'))
        else:
            flash('არასწორი მეილი ან პაროლი!', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# ადმინ პანელის გვერდი - მხოლოდ admin-ისთვის
@app.route('/admin-panel')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return "<h3>წვდომა შეზღუდულია!</h3>", 403
    users = User.query.all()
    orders = Order.query.all()
    return render_template('admin.html', users=users, orders=orders)

# ბაზის შექმნა
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)