from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column, composite, with_polymorphic
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from datetime import datetime
from functools import wraps
from forms import SignUpForm, LoginForm, ItemForm, BillingForm, OrderForm

# Grab current year - to be displayed in the footer
CURRENT_YEAR = datetime.now().year

# Load .env file with the SECRET_KEY
load_dotenv("./.env")

# Create Flask application instance
app = Flask(__name__)
# Create a database file called clothing.db or connect to it, if it already exists
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///clothing3.db"
# Set to False disables tracking modifications of objects and uses less memory
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Secret key allows Flask-Login to use sessions (allows one to store info specific to a
# user from one request to another) for authentication
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

# Packages Bootstrap CSS extension into the app
Bootstrap(app)
# SQLAlchemy
db = SQLAlchemy(app)

# LoginManager contains the code that lets your application and Flask - Login work together, such as how to
# load a user from an ID, where to send users when they need to log in, etc
login_manager = LoginManager()
# Configure actual application object for login
login_manager.init_app(app)


# Set up admin_only function decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If type of current user is not Owner, then abort with 403 error
        if current_user.type != "Owner":
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function


# Set up customer _only function decorator
def customer_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If type of current user is not Customer, then abort with 403 error
        if current_user.type != "Customer":
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function


# Table called 'placed_in' for the many-to-many relationship from item to order
# association_table = db.Table('placed_in',
#                              db.Column('item_id', db.ForeignKey('item.id'), primary_key=True),
#                              db.Column('order_num', db.ForeignKey('order.order_num'), primary_key=True)
#                              )


class PlacedIn(db.Model):
    __tablename__ = "placed_in"  # Table name
    item_id = db.Column(db.Integer, db.ForiegnKey('item.id'), primary_key=True)
    order_num = db.Column(db.Integer, db.ForeignKey('order.order_num'), primary_key=True)


# User Database Table
class User(UserMixin, db.Model):
    __tablename__ = "user"  # Table name
    # Fields
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email_address = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String)
    type = db.Column(db.String, nullable=False)

    # __mapper_args__ = {
    #     "polymorphic_on": type,
    #     'polymorphic_identity': 'user'
    # }
    #
    # def __repr__(self):
    #     return f"{self.__class__.__name__}({self.name!r})"

    # Establish one-to-many relationship from User to Warehouse
    warehouse = relationship("Warehouse", back_populates="user")

    # Establish one-to-many relationship from Owner to Item
    item = relationship("Item", back_populates="user")

    # Establish one-to-one relationship from Owner to Inventory
    # relationship.uselist flag indicates the placement of a scalar attribute instead of a collection on the “many”
    # side of the relationship.
    inventory = relationship("Inventory", uselist=False, back_populates="user")

    # Establish one-to-one relationship from Customer to Billing
    billing = relationship("Billing", uselist=False, back_populates="user")

    # Establish one-to-one relationship from Customer to Order
    order = relationship("Order", uselist=False, back_populates="user")

    # Establish many-to-one relationship from Customer to ShippingProvider
    shipping_provider_id = db.Column(db.Integer, db.ForeignKey("shipping_provider.id"))
    shipping_provider = relationship("ShippingProvider", back_populates="user")


# # Owner Database Table, specialization of User
# class Owner(User):
#     # __tablename__ = "owner"  # Table name
#     # Fields
#     id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
#
#     __mapper_args__ = {
#         'polymorphic_identity': 'owner'
#     }
#
#     # Establish one-to-many relationship from Owner to Warehouse
#     warehouse = relationship("Warehouse", back_populates="owner")
#
#     # Establish one-to-many relationship from Owner to Item
#     item = relationship("Item", back_populates="owner")
#
#     # Establish one-to-one relationship from Owner to Inventory
#     # relationship.uselist flag indicates the placement of a scalar attribute instead of a collection on the “many”
#     # side of the relationship.
#     inventory = relationship("Inventory", uselist=False, back_populates="owner")


# Owner Database Table, specialization of Customer
# class Customer(User):
#     # __tablename__ = "customer"  # Table name
#     # Fields
#     id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
#     shipping_address = db.Column(db.String(), nullable=False)
#
#     __mapper_args__ = {
#         'polymorphic_identity': 'customer'
#     }
#
#     # Establish one-to-one relationship from Customer to Billing
#     billing = relationship("Billing", uselist=False, back_populates="customer")
#
#     # Establish one-to-one relationship from Customer to Order
#     order = relationship("Order", uselist=False, back_populates="customer")
#
#     # Establish many-to-one relationship from Customer to ShippingProvider
#     shipping_provider_id = db.Column(db.Integer, db.ForeignKey("shipping_provider.id"))
#     shipping_provider = relationship("ShippingProvider", back_populates="customers")


class Warehouse(db.Model):
    __tablename__ = "warehouse"  # Table name
    # Fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)

    # Establish one-to-many relationship from Owner to Warehouse - creating a foreign key on the 'many' table warehouse,
    # that references the 'one' owner
    # foreign key is placed under the new field owner_id
    # "owner.id" The owner refers to the tablename of the Owner class.
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))  # adds new column in Warehouse for foreign key
    user = relationship("User", back_populates="warehouse")

    # Establish many-to-one relationship from Warehouse to Inventory
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'))
    inventory = relationship("Inventory", back_populates="warehouses")


class Inventory(db.Model):
    __tablename__ = "inventory"  # Table name
    # Fields
    id = db.Column(db.Integer, primary_key=True)
    stock = db.Column(db.Integer, nullable=False)
    last_updated = db.Column(db.String, nullable=False)

    # Establish many-to-one relationship from Warehouse to Inventory
    warehouses = relationship("Warehouse", back_populates="inventory")

    # Establish one-to-one relationship from Owner to Inventory
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship("User", back_populates="inventory")

    # Establish one-to-many relationship from Inventory to Item
    item = relationship("Item", back_populates="inventory")


class Item(db.Model):
    __tablename__ = "item"  # Field name
    # Fields
    id = db.Column(db.Integer, primary_key=True)
    img_url = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    sex = db.Column(db.String)
    size = db.Column(db.String)
    brand = db.Column(db.String)
    type = db.Column(db.String)
    weight = db.Column(db.Float)
    color = db.Column(db.String)

    # Establish one-to-many relationship from Owner to Item
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship("User", back_populates="item")

    # Establish one-to-many relationship from Inventory to Item
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'))
    inventory = relationship("Inventory", back_populates="item")

    # Establish many-to-many relationship from Item to Order
    order = relationship("Order", secondary=association_table, back_populates="items")


# class Color(db.Model):
#     # Multivalue attribute of color
#     __tablename__ = "color"  # Table name
#     # Fields
#     item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
#     color = db.Column(db.String, primary_key=True)


# Ignore this for now - likely scrap it
# class Review(db.Model):
# https://docs.sqlalchemy.org/en/14/orm/composites.html
#     __tablename__ = "review"
#     id = db.Column(db.Integer, primary_key=True)
#     comment = db.Column(db.String, nullable=False)
#     quality = db.Column(db.Integer)
#     durability = db.Column(db.Integer)
#     comfort = db.Column(db.Integer)
#     rating = composite()


class Billing(db.Model):
    __tablename__ = "billing"  # Table name
    # Fields
    card_number = db.Column(db.String, primary_key=True)
    expiry_date = db.Column(db.String)
    cvv = db.Column(db.String)

    # Establish one-to-one relationship from Customer to Billing
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship("User", back_populates="billing")


class Order(db.Model):
    __tablename__ = "order"  # Table name
    # Fields
    order_num = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.String)
    total_price = db.Column(db.Float)

    # Establish one-to-one relationship from Customer to Order
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship("User", back_populates="order")

    # Establish many-to-one relationship from Order to ShippingProvider
    shipping_provider_id = db.Column(db.Integer, db.ForeignKey('shipping_provider.id'))
    shipping_provider = relationship("ShippingProvider", back_populates="orders")

    # Establish many-to-many relationship from Item to Order
    items = relationship("Item", secondary=association_table, back_populates="order")


class ShippingProvider(db.Model):
    __tablename__ = "shipping_provider"  # Table name
    # Fields
    id = db.Column(db.Integer, primary_key=True)
    travel = db.Column(db.String, nullable=False)
    weight = db.Column(db.Float, nullable=False)

    # Establish many-to-one relationship from Customer to ShippingProvider
    user = relationship("User", back_populates="shipping_provider")

    # Establish many-to-one relationship from Order to ShippingProvider
    orders = relationship("Order", back_populates="shipping_provider")


with app.app_context():
    db.create_all()  # Create database


@login_manager.user_loader
def load_user(user_id):
    # Reload the user object from the user ID stored in the session
    return User.query.get(int(user_id))


@app.route('/')
def home():
    items = Item.query.all()  # Query all items from Item Table
    clothing_types = []   # Array to store the unique clothing types
    # For each item in queried items...
    for item in items:
        # If the item type is not already in clothing_types array, add it to clothing_types
        if item.type not in clothing_types:
            clothing_types.append(item.type)
    # Sort clothing_types array alphabetically
    clothing_types = sorted(clothing_types, key=str.lower)

    # If user is logged in already, render index.html with the following arguments
    if current_user.is_authenticated:
        # return redirect(url_for("dashboard", username=current_user.username))
        return render_template("index.html", all_items=items, all_types=clothing_types,
                               current_user=current_user, current_year=CURRENT_YEAR)

    # If no user is logged in, render index.html with the following arguments
    return render_template("index.html", all_items=items, all_types=clothing_types, current_year=CURRENT_YEAR)


@app.route('/sign-up', methods=["GET", "POST"])
def sign_up():
    sign_up_form = SignUpForm()  # Create an instance of the SignUpForm
    if sign_up_form.validate_on_submit():  # If a Submit button is clicked and a POST request is made...
        # If a User with the same email address is already created ...
        if User.query.filter_by(email_address=sign_up_form.email.data).first():
            # Display the following message above the form
            flash("Sorry, this email has already been registered. Please log in instead.")
            # Redirect to the login route
            return redirect(url_for("login"))
        # If no Customer with that email address is found, create a new Customer
        new_user = User()
        # Set username of new_customer to the one entered in the sign up form
        new_user.username = sign_up_form.username.data
        # Set password of new_customer to the one entered in the sign up form after hashing it
        new_user.password = generate_password_hash(sign_up_form.password.data, method="pbkdf2:sha256", salt_length=8)
        # Set email_address of new_customer to the one entered in the sign up form
        new_user.email_address = sign_up_form.email.data
        new_user.phone_number = sign_up_form.phone_number.data
        new_user.type = sign_up_form.type.data
        new_user.shipping_provider_id = 1
        # Add new_customer to the Database
        db.session.add(new_user)
        # Commit changes
        db.session.commit()

        # Create new Billing and populate it with the corresponding info from the sign up form
        new_billing = Billing(
            card_number=sign_up_form.card_number.data,
            expiry_date=sign_up_form.expiry_date.data,
            cvv=sign_up_form.cvv.data,
            user_id=new_user.id
        )
        new_order = Order(
            user_id=new_user.id
        )
        # Add new_billing to the database
        db.session.add(new_billing)
        # Commit changes
        db.session.commit()
        # Log new_customer in
        login_user(new_user)
        return redirect(url_for("home", username=current_user.username))
        # if sign_up_form.type == "Owner":  # If the user type in sign up form is Owner...
        #     # If an Owner with the same email address is already created ...
        #     if User.query.filter_by(email_address=sign_up_form.email.data).first():
        #         # Display the following message above the form
        #         flash("Sorry, this email has already been registered. Please log in instead.")
        #         # Redirect to the login route
        #         return redirect(url_for("login"))
        #     # If no Owner with that email address is found, create a new Owner
        #     new_owner = Owner()
        #     # Set username of new_owner to the one entered in the sign up form
        #     new_owner.username = sign_up_form.username.data
        #     # Set password of new_owner to the one entered in the sign up form after hashing it
        #     new_owner.password = generate_password_hash(sign_up_form.password.data, method="pbkdf2:sha256",
        #                                                 salt_length=8)
        #     # Set email_address of new_owner to the one entered in the sign up form
        #     new_owner.email_address = sign_up_form.email.data
        #     # Add new_owner to the Database
        #     db.session.add(new_owner)
        #     # Commit changes
        #     db.session.commit()
        #     # Log new_owner in
        #     login_user(new_owner)
        #     # Redirect to home route
        #     return redirect(url_for("home", username=current_user.username))
        # # If user type in sign up form is Customer...
        # if sign_up_form.type == "Customer":
        #     # If a Customer with the same email address is already created ...
        #     if Customer.query.filter_by(email_address=sign_up_form.email.data).first():
        #         # Display the following message above the form
        #         flash("Sorry, this email has already been registered. Please log in instead.")
        #         # Redirect to the login route
        #         return redirect(url_for("login"))
        #     # If no Customer with that email address is found, create a new Customer
        #     new_customer = Customer()
        #     # Set username of new_customer to the one entered in the sign up form
        #     new_customer.username = sign_up_form.username.data
        #     # Set password of new_customer to the one entered in the sign up form after hashing it
        #     new_customer.password = generate_password_hash(sign_up_form.password.data, method="pbkdf2:sha256",
        #                                                    salt_length=8)
        #     # Set email_address of new_customer to the one entered in the sign up form
        #     new_customer.email_address = sign_up_form.email.data
        #     # Add new_customer to the Database
        #     db.session.add(new_customer)
        #     # Commit changes
        #     db.session.commit()
        #
        #     # Create new Billing and populate it with the corresponding info from the sign up form
        #     new_billing = Billing(
        #         card_number=sign_up_form.card_number.data,
        #         expiry_date=sign_up_form.expiry_date.data,
        #         cvv=sign_up_form.cvv.data,
        #         customer_id=new_customer.id
        #     )
        #     # Add new_billing to the database
        #     db.session.add(new_billing)
        #     # Commit changes
        #     db.session.commit()
        #     # Log new_customer in
        #     login_user(new_customer)
        #     return redirect(url_for("home", username=current_user.username))
    # If GET request, simply render signup.html with the following arguments
    return render_template("signup.html", form=sign_up_form, current_user=current_user, current_year=CURRENT_YEAR)


@app.route('/login', methods=["GET", "POST"])
def login():
    # Create an instance of the LoginForm
    login_form = LoginForm()
    # If a Submit button is clicked and a POST request is made...
    if login_form.validate_on_submit():
        # Grab email from the login form
        login_email = login_form.email.data
        # Grab password from the login form
        login_password = login_form.password.data
        # Not sure how specialized user classes work with login...
        requested_user = User.query.filter_by(email_address=login_email).first()
        # If a user/owner/customer with the corresponding email address is found...
        if requested_user:
            # Check the hash of the entered password. If it matches the one in the database...
            if check_password_hash(pwhash=requested_user.password, password=login_password):
                # Log in the user
                login_user(requested_user)
                # Redirect to home route
                return redirect(url_for("home", username=current_user.username))
            else:
                # Otherwise, display a message indicating wrong password
                flash("Sorry, wrong password! Please try again.")
                # Redirect to login route
                return redirect(url_for("login"))
        else:
            # If no corresponding email address is found, display a message
            flash("Sorry, that email does not exist! Please try again.")
            # Redirect to login route
            return redirect(url_for("login"))
    # If GET request, simply render login.html with the following arguments
    return render_template("login.html", form=login_form, current_user=current_user,
                           current_year=CURRENT_YEAR)


@app.route('/owner-add-item', methods=["GET", "POST"])
@admin_only
@login_required
def owner_add_item():
    # Create an instance of the ItemForm
    owner_add_item_form = ItemForm()
    # If a Submit button is clicked and a POST request is made...
    if owner_add_item_form.validate_on_submit():
        # Grab item name from the item form
        new_item_name = owner_add_item_form.name.data
        # If an item with the same name already exists...
        if Item.query.filter_by(name=new_item_name).first():
            # Display a message indicating item already exists
            flash("Sorry! You already have an item with this name. Please enter another one.")
            # Redirect back to the owner-add-item route
            return redirect(url_for("owner_add_item"))
        # If item doesn't already exist in the database, create a new item
        # Initialize fields of this new item with the information entered in the item form
        item_to_add = Item(
            name=new_item_name,
            img_url=owner_add_item_form.img_url.data,
            price=owner_add_item_form.price.data,
            sex=owner_add_item_form.sex.data,
            size=owner_add_item_form.size.data,
            brand=owner_add_item_form.brand.data,
            type=owner_add_item_form.type.data,
            weight=owner_add_item_form.weight.data,
            color=owner_add_item_form.color.data,
            user_id=current_user.id,
            inventory_id=1
        )
        # Add new item to database
        db.session.add(item_to_add)
        # Commit changes
        db.session.commit()

        # Grab colors from the form
        # new_colors = owner_add_item_form.colors.data
        # # For each color in new_colors, add the color and item id to the Colors table
        # for new_color_name in new_colors:
        #     color_to_add = Color(color=new_color_name, item_id=item_to_add.id)
        #     db.session.add(color_to_add)
        #     db.session.commit()  # Commit Changes

        # Redirect to home route
        return redirect(url_for("home", username=current_user.username))
    # If GET request, simply render add-item.html with the following arguments
    return render_template("add-item.html", form=owner_add_item_form, operation="Add", current_user=current_user,
                           current_year=CURRENT_YEAR)


@app.route('/edit-item/<int:item_id>', methods=["GET", "POST"])
@admin_only
@login_required
def edit_item(item_id):
    # Query for the item to edit using the item_id argument
    item_to_edit = Item.query.get(item_id)
    # Create an instance of the ItemForm with the fields pre-loaded with the
    # values from item_to_edit
    edit_form = ItemForm(
        name=item_to_edit.name,
        img_url=item_to_edit.img_url,
        price=item_to_edit.price,
        sex=item_to_edit.sex,
        size=item_to_edit.size,
        brand=item_to_edit.brand,
        type=item_to_edit.type,
        weight=item_to_edit.weight,
        color=item_to_edit.color
    )
    # If a Submit button is clicked and a POST request is made...
    if edit_form.validate_on_submit():
        # Grab item name from the item form
        # new_item_name = edit_form.name.data
        # Check item with the same name already exists. If so...
        # if Item.query.filter_by(name=new_item_name).first():
        #     # Display a message indicating item already exists
        #     flash("Sorry! You already have an item with this name. Please enter another one.")
        #     # Redirect back to the edit-item route
        #     return redirect(url_for("edit_item", item_id=item_id))
        # Grab colors from the form
        # new_colors = edit_form.colors.data
        # For each color in new_colors, check if a record with the same color name and item_id exist
        # for new_color_name in new_colors:
        #     if Color.query.filter_by(color=new_color_name, item_id=item_id).first():
        #         # Display message indicating the item-color combo already exists
        #         flash(f"Sorry! There is already an item with this color: {new_color_name} Please enter another one.")
        #         # Redirect back to the edit-item route
        #         return redirect(url_for("edit_item", item_id=item_id))

        # If item-color combo doesn't exist, update the fields of the item in the database
        item_to_edit.name = edit_form.name.data
        item_to_edit.img_url = edit_form.img_url.data
        item_to_edit.price = edit_form.price.data
        item_to_edit.sex = edit_form.sex.data
        item_to_edit.size = edit_form.size.data
        item_to_edit.brand = edit_form.brand.data
        item_to_edit.type = edit_form.type.data
        item_to_edit.weight = edit_form.weight.data
        item_to_edit.color = edit_form.color.data
        # Commit Changes
        db.session.commit()

        # For each color in new_colors, add the color and item_id to the Colors table
        # for new_color_name in new_colors:
        #     color_to_add = Color(color=new_color_name, item_id=item_id)
        #     db.session.add(color_to_add)
        #     db.session.commit() # Commit Changes

        # Redirect to home route
        return redirect(url_for("home", username=current_user.username))
    # If GET request, simply render add-item.html with the following arguments
    return render_template("add-item.html", form=edit_form, operation="Edit", current_user=current_user,
                           current_year=CURRENT_YEAR)


@app.route('/delete-item/<int:item_id>')
@admin_only
@login_required
def delete_item(item_id):
    # Query for the item to be deleted using item_id argument
    item_to_delete = Item.query.get(item_id)
    # Query for all colors for that item in the colors table
    # all_colors = Color.query.filter_by(item_id=item_id).all()
    # # For each color in the queried colors, delete the record from the colors table
    # for color in all_colors:
    #     if color.item_id == item_to_delete.id:
    #         db.session.delete(color)
    #         db.session.commit()
    # Delete the item from the items table in the database
    db.session.delete(item_to_delete)
    db.session.commit()  # Commit changes
    # Redirect to home route
    return redirect(url_for("home", username=current_user.username))


@app.route('/customer-add-item/<int:item_id>', methods=["GET", "POST"])
@customer_only
@login_required
def customer_add_item(item_id):

    # Item to be added to the customer's order using the item_id argument
    item_to_add = Item.query.get(item_id)
    # Create instance of the item form with pre-populated values of the item that was clicked
    customer_add_item_form = ItemForm(
        name=item_to_add.name,
        img_url=item_to_add.img_url,
        price=item_to_add.price,
        sex=item_to_add.sex,
        size=item_to_add.size,
        brand=item_to_add.brand,
        type=item_to_add.type,
        weight=item_to_add.weight,
    )
    # If the Submit button is clicked and a POST request is made
    if customer_add_item_form.validate_on_submit():
        # Grab name from the form
        item_name = customer_add_item_form.name.data
        # If an Order already exists for that customer and the Item exists...
        if Order.query.filter_by(user_id=current_user.id).first() and Item.query.get(name=item_name):
            # Query for the matching order for that customer
            matching_order = Order.query.filter_by(user_id=current_user.id)
            # Query for the matching item to be added
            matching_item = Item.query.get(name=item_name)
            # Add a new record to the "placed_in" table using the primary keys of the order and item found
            item_order_combo_to_add = PlacedIn(item_id=matching_item.id, order_num=matching_order.order_num)
            db.session.add(item_order_combo_to_add)
            # # item_order_combo = Item.query.join(association_table).join(Order).\
            # #     filter((association_table.c.item_id == matching_item.id) &
            # #            (association_table.c.order_num == matching_order.order_num)).all()
            #
            # statement = association_table.insert().values(item_id=matching_item.id, user_id=matching_order.id)
            # db.session.execute(statement)
            db.session.commit()
            # new_item_order_combo = association_table(item_id=matching_item.id, order_num=matching_order.order_num)
            # db.session.add(new_item_order_combo)
            # Commit Changes
            # db.session.commit()

            # Create variable for total price of the items in the order
            total_price = 0
            all_item_order_combos = PlacedIn.query.filter_by(order_num=current_user.id)
            # all_item_order_combos = Item.query.join(association_table).join(Order).\
            #     filter((association_table.c.order_num == matching_order.order_num)).all()
            # For each item-order combo in the records of the "placed_in" that are in the order...
            for item_order in all_item_order_combos:
                # Query for the item, grab it's price, and add it to the total price
                item = Item.query.get(id=item_order.item_id)
                total_price += float(item.price)

            # Query for the order to be edited
            order_to_edit = Order.query.get(matching_order.order_num)
            # Update the total_price with the new one that was just calculated
            order_to_edit.total_price = total_price
            # Commit changes
            db.session.commit()

            # Display message indicating item was added to order
            flash("Item added to order!")
            # Redirect to view_order page
            return redirect(url_for("view_order"))
        else:
            # If order doesn't yet exist for that customer, create a new order with the following values
            new_order = Order(
                order_date=datetime.now().strftime('%B %d, %Y at %I:%M%p'),
                total_price=0,
                user_id=current_user.id,
                shipping_provider_id=1
            )
            # Add new order to database and commit changes
            db.session.add(new_order)
            db.session.commit()
            # Query for the matching item to be added
            matching_item = Item.query.get(name=item_name)
            # Add a new record to the "placed_in" table using the primary keys of the new order and item found
            # new_item_order_combo = association_table(item_id=matching_item.id, order_num=new_order.order_num)
            # db.session.add(new_item_order_combo)
            # db.session.commit()  # Commit changes

            # item_order_combo = Item.query.join(association_table).join(Order).\
            #     filter((association_table.c.item_id == matching_item.id) &
            #            (association_table.c.order_num == matching_order.order_num)).all()

            # statement = association_table.insert().values(item_id=matching_item.id, user_id=new_order.id)
            # db.session.execute(statement)
            # db.session.commit()
            # Create variable for total price of the items in the order
            total_price = 0
            all_item_order_combos = Item.query.join(association_table).join(Order). \
                filter((association_table.c.order_num == new_order.order_num)).all()
            # For each item-order combo in the records of the "placed_in" that are in the order...
            for item_order in all_item_order_combos:
                # Query for the item, grab it's price, and add it to the total price
                item = Item.query.get(id=item_order.item_id)
                total_price += float(item.price)

            # Query for the order to be edited
            order_to_edit = Order.query.get(new_order.order_num)
            # Update the total_price with the new one that was just calculated
            order_to_edit.total_price = total_price
            # Commit changes
            db.session.commit()
            # Display message indicating item was added to order
            flash("Item added to order!")
            # Redirect to view_order route
            return redirect(url_for("view_order"))
    # If GET request, simply render customer-add-item.html with the following arguments
    return render_template("customer-add-item.html", form=customer_add_item_form, operation="Add",
                           current_user=current_user, current_year=CURRENT_YEAR)


@app.route('/view-order', methods=["GET", "POST"])
@customer_only
@login_required
def view_order():
    order_price = 0  # total_price of the items
    order_items = []  # Items in the customers order, to be displayed
    # Query for the Order with the customer_id that matches that of the current user
    order_to_view = Order.query.filter_by(user_id=current_user.id).first()
    # Query for all item-order combos in the "placed_in" table that matches the order_num of the queried order
    all_item_order_combos = Item.query.join(association_table).join(Order). \
        filter((association_table.c.order_num == order_to_view.order_num)).all()
    # For each item-order combo in the records of the "placed_in" that are in the order...
    for item_order in all_item_order_combos:
        # Query for the item, grab it's price, and add it to the total price
        item = Item.query.get(id=item_order.item_id)
        order_price += float(item.price)
        order_items.append(item)
    # item_order_combos = association_table.query.filter_by(order_id=order_to_view.order_num).all()
    # For each item-order combo in the queried item-order combos...
    # for combo in item_order_combos:
    #     # Query for the item that matches the item_id in that combo and append the item to order_items
    #     order_items.append(Item.query.get(item_id=combo.item_id))
    #     order_price += float(Item.query.get(item_id=combo.item_id).price)
    order_form = OrderForm(
        order_price=order_price
    )
    if order_form.validate_on_submit():
        # delete all items in the order
        records_to_delete = Item.query.join(association_table).join(Order). \
            filter((association_table.c.order_num == order_to_view.order_num)).all()
        for record in records_to_delete:
            db.session.delete(record)
            db.session.commit()  # Commit changes
        order_to_delete_from = Order.query.filter_by(user_id=current_user.id).first()
        # Delete the item_order combo in the placed_in table with the item_id that matches the queried item

        return render_template("order-submitted.html", current_user=current_user,
                               current_year=CURRENT_YEAR)

    # Render view-order.html with the order_items passed to it
    return render_template("view-order.html", form=order_form, order_items=order_items, current_user=current_user,
                           current_year=CURRENT_YEAR, order_price=order_price)


@app.route('/delete-order-item/<int:item_id>')
@customer_only
@login_required
def delete_order_item(item_id):
    # Query for the item to be removed from the order using item_id argument
    item_to_delete = Item.query.get(item_id)
    # Use filter_by instead of get if you want to query with a non-primary key field
    order_to_delete_from = Order.query.filter_by(user_id=current_user.id).first()
    # Delete the item_order combo in the placed_in table with the item_id that matches the queried item
    record_to_delete = Item.query.join(association_table).join(Order). \
        filter((association_table.c.item_id == item_to_delete.id) &
               (association_table.c.order_num == order_to_delete_from.order_num)).all()
    # record_to_delete = association_table.query.get(item_id=item_to_delete.item_id)
    db.session.delete(record_to_delete)
    db.session.commit()  # Commit changes
    # Redirect to view_order route
    return redirect(url_for("view_order", username=current_user.username))


@app.route('/edit-billing/<int:user_id>', methods=["GET", "POST"])
@customer_only
@login_required
def edit_billing(user_id):
    # Query for the billing info to be edited
    billing_to_edit = Billing.query.filter_by(user_id=user_id).first()
    # Create instance of the BillingForm and pre-populate the fields with the existing info in the DB
    billing_form = BillingForm(
        card_number=billing_to_edit.card_number,
        expiry_date=billing_to_edit.expiry_date,
        cvv=billing_to_edit.cvv
    )
    # If the Submit button is clicked and a POST request is made...
    if billing_form.validate_on_submit():
        # Update the fields of the billing to be edited
        billing_to_edit.card_number = billing_form.card_number.data
        billing_to_edit.expiry_date = billing_form.expiry_date.data
        billing_to_edit.cvv = billing_form.cvv.data
        # Commit changes
        db.session.commit()
        # Redirect to edit_billing route
        return redirect(url_for("edit_billing", username=current_user.username))
    # If GET request, simply render add-billing.html with the following arguments
    return render_template("add-billing.html", form=billing_form, current_user=current_user,
                           current_year=CURRENT_YEAR)


@app.route("/logout")
@login_required
def logout():
    # Logout user
    logout_user()
    # Redirect to home route
    return redirect(url_for("home", current_user=current_user))


# Run app
if __name__ == "__main__":
    app.run(debug=True)
