from datetime import datetime, date
from functools import wraps
import pandas
import smtplib
from os import environ
from email.message import EmailMessage
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from geojson import Point, Feature, FeatureCollection
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, LandlordForm, UpdateLandlordForm, ContactForm


app = Flask(__name__)
app.config['SECRET_KEY'] = environ['SECRET_KEY']
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# LOGIN SETUP
login_manager = LoginManager()
login_manager.init_app(app)

# gravatar image thing
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)

# image upload stuff
UPLOAD_PATH = 'static/'
xcel_path = 'xcel/'
images_path = 'img/uploaded_images/'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXCEL = {"xlsx"}
app.config['UPLOAD_FOLDER'] = UPLOAD_PATH


# #CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    play_game_page = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    project_type = db.Column(db.String(10), nullable=True)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250))  # image for the top of the site
    # parent of Comment objects
    comments = relationship('Comment', back_populates="parent_post")
    # parent of Image objects
    images = relationship('Image', back_populates='parent_post')
    # child of User object
    author_id = db.Column(db.Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    # parent of BlogPost object
    posts = relationship('BlogPost', back_populates="author")
    # parent of Comment object
    comments = relationship('Comment', back_populates="commenter")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    # child of User object relationship
    commenter = relationship("User", back_populates="comments")
    commenter_id = db.Column(db.Integer, ForeignKey('users.id'))
    # child of BlogPost object relationship
    parent_post = relationship("BlogPost", back_populates="comments")
    post_id = db.Column(db.Integer, ForeignKey('blog_posts.id'))


class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    img_url = db.Column(db.String(300), nullable=False)
    # a one to many to blog posts the same way that comments are
    parent_post = relationship("BlogPost", back_populates="images")
    post_id = db.Column(db.Integer, ForeignKey('blog_posts.id'))


class Location(db.Model):
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(200), nullable=False)
    lattitude = db.Column(db.String(50), nullable=False)
    longitude = db.Column(db.String(50), nullable=False)


# set up database and property records
db.create_all()
prop_records = pandas.read_excel('static/xcel/currentproperties.xlsx').to_dict('records')



# Regular Functions
def send_email(email_address, name, email_content):
    email = EmailMessage()
    email['from'] = email_address
    email['to'] = environ['MY_EMAIL']
    email['subject'] = name
    email.set_content("<body>" + name + " " + " " + email_content + "</body>")
    with smtplib.SMTP(host='smtp.gmail.com', port=587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(environ['MAILER'], environ['MAILER_PASSWORD'])
        smtp.send_message(email)


def make_list_items_strings(list_object):
    new_list = []
    for obj in list_object:
        if obj is None:
            obj = ""
            new_list.append(obj)
        elif pandas.isna(obj):
            obj = ""
            new_list.append(obj)
        elif type(obj) == float:
            new_list.append(str(int(obj)))
        else:
            new_list.append(obj)
    return new_list


def allowed_file(filename, allowed_ext_set):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_ext_set


def save_images(form, post):
    first_image = True
    for image in form.images.data:
        if allowed_file(image.filename, ALLOWED_IMAGE_EXTENSIONS):
            filename = secure_filename(image.filename)
            image.save(app.config['UPLOAD_FOLDER'] + images_path + filename)
            img_url = 'img/uploaded_images/' + filename
            blog_image = Image(img_url=img_url,
                               parent_post=post
                               )
            db.session.add(blog_image)
            if first_image:
                post.img_url = img_url
                first_image = False
            db.session.commit()


def save_comment(form, requested_post):
    new_comment = Comment(text=form.body.data,
                          commenter_id=current_user.id,
                          parent_post=requested_post
                          )
    db.session.add(new_comment)
    db.session.commit()


def salt_hash_store_new_user(form):
    password = form.password.data
    salty_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
    user = User(email=form.email.data,
                password=salty_hash,
                name=form.name.data
                )
    db.session.add(user)
    db.session.commit()
    return user


def delete_all_users():
    all_users = db.session.query(User).all()
    for user in all_users:
        db.session.delete(user)
        db.session.commit()


# delete_all_users()


def admin_only(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            if current_user.id == 1:
                return function(*args, **kwargs)
            else:
                return abort(403, description="Admins only dawg")
        except AttributeError:
            return abort(403, description="Admins only dawg")
    return wrapper


# APP ROUTES
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/update-landlord", methods=["POST", "GET"])
@admin_only
def update_landlord_data():
    form = UpdateLandlordForm()
    if form.validate_on_submit():
        # get and save our file with date name
        excel_file = form.excel.data
        if allowed_file(excel_file.filename, ALLOWED_EXCEL):

            # save the old file for posterity and to eventually make graphs with
            data = pandas.read_excel('static/xcel/currentproperties.xlsx')
            d = datetime.now()
            date_name = d.strftime("%B") + d.strftime("%Y")
            old_filename = f'static/xcel/old/recordsfrombefore{date_name}.xlsx'
            data.to_excel(old_filename)

            # save the new file
            filename = secure_filename('currentproperties.xlsx')
            file_path = app.config['UPLOAD_FOLDER'] + xcel_path + filename
            excel_file.save(file_path)

            # load the new file to be used for queries
            global prop_records
            prop_records = pandas.read_excel('static/xcel/currentproperties.xlsx').to_dict('records')
            flash("Lol i think it worked")
            return redirect(url_for('landpeasant'))
        else:
            flash("file not allowed")
            return redirect(url_for('landpeasant'))
    return render_template("update_landlord.html", form=form)


@app.route("/landpeasant", methods=["POST", "GET"])
def land_peasant():
    form = LandlordForm()
    if form.validate_on_submit():
        owner_addy = None
        owned_properties_list = []
        entered_address_dir = " ".join([form.number.data,
                                        form.direction.data,
                                        form.street.data.upper(),
                                        form.st_type.data
                                        ])
        entered_address_sans_dir = " ".join([form.number.data,
                                             "",
                                             form.street.data.upper(),
                                             form.st_type.data
                                             ])
        for record in prop_records:
            address = " ".join(make_list_items_strings([record["SITE_NBR"],
                                                        record["SITE_DIR"],
                                                        record["SITE_NAME"],
                                                        record["SITE_MODE"]
                                                        ]))
            if address == entered_address_dir or address == entered_address_sans_dir:
                owner_addy = " ".join(make_list_items_strings([record["OWNER_NUM"],
                                                               record["OWNER_DIR"],
                                                               record["OWNER_ST"],
                                                               record["OWNER_TYPE"]
                                                               ]))
                break
        if owner_addy is None:
            flash("No records for that address")
            return render_template("landlord.html", form=form)
        else:
            for record in prop_records:
                address_owner = " ".join(make_list_items_strings([record["OWNER_NUM"],
                                                                  record["OWNER_DIR"],
                                                                  record["OWNER_ST"],
                                                                  record["OWNER_TYPE"]
                                                                  ]))
                if address_owner == owner_addy:
                    address = " ".join(make_list_items_strings([record["SITE_NBR"],
                                                                record["SITE_DIR"],
                                                                record["SITE_NAME"],
                                                                record["SITE_MODE"]
                                                                ]))
                    full_owner_address = " ".join([owner_addy, record["OWNER_CITY"], record["OWNER_STATE"], record["OWNER_ZIP"]])
                    add_loc = Location.query.filter_by(address=address).first()
                    location = Point((float(add_loc.longitude), float(add_loc.lattitude)))
                    feature = Feature(geometry=location, properties={"owner": record["OWNER"],
                                                                     "property_address": address,
                                                                     "tax_address": full_owner_address,
                                                                     "property_taxes": make_list_items_strings([record['ASMT_TAXABLE']])[0],
                                                                     "property_value": make_list_items_strings([record['TOTAL_VALUE']])[0],
                                                                     "more_info": make_list_items_strings([record["SITE_MORE"]])[0]
                                                                     })
                    owned_properties_list.append(feature)
            feature_collection = FeatureCollection(owned_properties_list)
            return render_template("map.html", addresses=feature_collection)
    return render_template("landlord.html", form=form)


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    #  below we're just reversing the posts so they will appear on the site from newest to oldest because they are stored oldest to newest
    post_list = []
    for post in posts:
        post_list.append(post)
    post_list.reverse()
    return render_template("index.html", all_posts=post_list)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.passwordtwo.data:
            flash("passwords don't match, try again")
            return redirect(url_for('register'))
        user_email = form.email.data
        if User.query.filter_by(email=user_email).first():
            flash(f"please use {user_email} to log in")
            return redirect(url_for('login'))
        user = salt_hash_store_new_user(form)
        login_user(user)
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)


@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_email = form.email.data
        user = User.query.filter_by(email=user_email).first()
        if user:
            entered_password = form.password.data
            if check_password_hash(user.password, entered_password):
                login_user(user)
                flash("Successful login dawg")
                return redirect(url_for('get_all_posts'))
            else:
                flash("Wrong Password")
                return redirect(url_for("login"))
        else:
            flash(f"{user_email} is not a registered user")
            return redirect(url_for('register'))

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if form.validate_on_submit():
        if current_user.is_authenticated:
            save_comment(form, requested_post)
            return redirect(url_for("show_post", post_id=post_id))
        else:
            flash("You need to Login to post comments dawg")
            return redirect(url_for("login"))
    return render_template("post.html", post=requested_post, form=form)


@app.route("/play_game/<play_game_page>")
def play_game(play_game_page):
    return render_template(play_game_page)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["POST", "GET"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        send_email(form.email.data, form.name.data, form.body.data)
        return redirect(url_for('get_all_posts'))
    return render_template("contact.html", form=form)


@app.route("/new-post", methods=["POST", "GET"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            project_type=form.project_type.data,
            play_game_page=form.play_game_page.data,
            body=form.body.data,
            author=current_user,
            img_url="place holder string",
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        if form.images.data:
            save_images(form, new_post)
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["POST", "GET"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.body = edit_form.body.data
        post.project_type = edit_form.project_type.data
        if edit_form.images.data:
            save_images(edit_form, post)
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/delete_image<int:post_id>/<int:img_id>")
@admin_only
def delete_image(post_id, img_id):
    img_to_delete = Image.query.get(img_id)
    db.session.delete(img_to_delete)
    db.session.commit()
    return redirect(url_for('show_post', post_id=post_id))


if __name__ == "__main__":
    app.run()
