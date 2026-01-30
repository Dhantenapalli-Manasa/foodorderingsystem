from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'food-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ===================== MODELS =====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category = db.Column(db.String(50))
    image = db.Column(db.String(200))


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'))
    quantity = db.Column(db.Integer, default=1)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    food_name = db.Column(db.String(100))
    price = db.Column(db.Float)


# ===================== LOGIN LOADER =====================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ===================== ROUTES =====================

@app.route('/')
def home():
    foods = Food.query.all()
    return render_template('index.html', foods=foods)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('register'))

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash("Invalid credentials")

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    foods = Food.query.all()
    return render_template('dashboard.html', foods=foods)


@app.route('/add_to_cart/<int:food_id>')
@login_required
def add_to_cart(food_id):
    item = Cart.query.filter_by(user_id=current_user.id, food_id=food_id).first()

    if item:
        item.quantity += 1
    else:
        cart = Cart(user_id=current_user.id, food_id=food_id)
        db.session.add(cart)

    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/cart')
@login_required
def cart():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    return render_template('cart.html', items=items, Food=Food)


@app.route('/place_order')
@login_required
def place_order():
    items = Cart.query.filter_by(user_id=current_user.id).all()

    for item in items:
        food = Food.query.get(item.food_id)
        order = Order(user_id=current_user.id, food_name=food.name, price=food.price)
        db.session.add(order)
        db.session.delete(item)

    db.session.commit()
    return redirect(url_for('orders'))


@app.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('orders.html', orders=orders)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# ===================== RUN =====================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if Food.query.count() == 0:
            db.session.add(Food(
                name="Burger",
                description="Cheese Burger",
                price=120,
                category="Fast Food",
                image="burger.jpg"
            ))
            db.session.add(Food(
                name="Pizza",
                description="Veg Pizza",
                price=250,
                category="Fast Food",
                image="pizza.jpg"
            ))
            db.session.add(Food(
                name="Biryani",
                description="Chicken Biryani",
                price=180,
                category="Main Course",
                image="biryani.jpg"
            ))
            db.session.commit()

    app.run(debug=True)
