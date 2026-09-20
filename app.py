"""Thought Trail blog application."""

import os
import secrets
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
SITE_LINKS = {
    "insta_url": os.environ.get("INSTAGRAM_URL", "#"),
    "link_url": os.environ.get("LINKEDIN_URL", "#"),
    "git_url": os.environ.get("GITHUB_URL", "#"),
}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-local-development-key"),
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'blog.db'}").replace("postgres://", "postgresql+psycopg://", 1).replace("postgresql://", "postgresql+psycopg://", 1),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_FOLDER=os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "static" / "assets" / "img")),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
)
Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
db = SQLAlchemy(app)


class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(800), nullable=False)
    author = db.Column(db.String(800), nullable=False)
    slug = db.Column(db.String(800), nullable=False, unique=True, index=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    img_file = db.Column(db.String(120), nullable=False)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(800), nullable=False)
    email = db.Column(db.String(800), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    msg = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


@app.context_processor
def inject_globals():
    return {"csrf_token": csrf_token, "paras": SITE_LINKS}


@app.before_request
def protect_post_requests():
    if request.method == "POST" and request.form.get("csrf_token") != session.get("csrf_token"):
        abort(400, "Invalid or missing CSRF token.")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("auth"))
        return view(*args, **kwargs)

    return wrapped


def valid_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_image(uploaded):
    """Save an allowed image with a collision-resistant filename."""
    filename = f"{secrets.token_hex(8)}-{secure_filename(uploaded.filename)}"
    uploaded.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return filename


@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        expected_username = os.environ.get("ADMIN_USERNAME")
        password_hash = os.environ.get("ADMIN_PASSWORD_HASH")
        if expected_username and password_hash and username == expected_username and check_password_hash(password_hash, password):
            session.clear()
            session["is_admin"] = True
            csrf_token()
            return redirect(url_for("dashboard"))
        return render_template("auth.html", error="Invalid username or password."), 401
    return render_template("auth.html")


@app.route("/dashboard")
@admin_required
def dashboard():
    return render_template("dashboard.html", posts=Post.query.order_by(Post.date.desc()).all())


@app.route("/edit/<int:sno>", methods=["GET", "POST"])
@admin_required
def edit(sno):
    post = None if sno == 0 else db.get_or_404(Post, sno)
    if request.method == "POST":
        fields = {name: request.form.get(name, "").strip() for name in ("title", "slug", "content", "author")}
        uploaded = request.files.get("image")
        if uploaded and uploaded.filename:
            if not valid_image(uploaded.filename):
                flash("Choose a PNG, JPG, JPEG, GIF, or WEBP image under 5 MB.", "danger")
                return render_template("edit.html", post=post, sno=sno), 400
            fields["img_file"] = save_image(uploaded)
        else:
            fields["img_file"] = request.form.get("img_file", "").strip()
        if not all(fields.values()):
            flash("All post fields and a background image are required.", "danger")
            return render_template("edit.html", post=post, sno=sno), 400
        duplicate = Post.query.filter(Post.slug == fields["slug"], Post.sno != sno).first()
        if duplicate:
            flash("That slug is already in use.", "danger")
            return render_template("edit.html", post=post, sno=sno), 400
        if post is None:
            post = Post(**fields)
            db.session.add(post)
        else:
            for name, value in fields.items():
                setattr(post, name, value)
        db.session.commit()
        flash("Post saved.", "success")
        return redirect(url_for("edit", sno=post.sno))
    return render_template("edit.html", post=post, sno=sno)


@app.route("/")
def home():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.date.desc()).paginate(page=max(page, 1), per_page=5, error_out=False)
    return render_template("index.html", posts=posts.items, next=posts.next_num if posts.has_next else None)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        entry = Contact(name=request.form.get("name", "").strip(), email=request.form.get("email", "").strip(), phone=request.form.get("phone", "").strip(), msg=request.form.get("message", "").strip())
        if not all((entry.name, entry.email, entry.phone, entry.msg)):
            flash("Please complete every field.", "danger")
        else:
            db.session.add(entry)
            db.session.commit()
            flash("Thanks — your message was sent.", "success")
            return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/post/<post_slug>")
def post(post_slug):
    return render_template("post.html", post=Post.query.filter_by(slug=post_slug).first_or_404())


@app.route("/uploader", methods=["POST"])
@admin_required
def uploader():
    uploaded = request.files.get("file1")
    if not uploaded or not uploaded.filename or not valid_image(uploaded.filename):
        flash("Upload a PNG, JPG, JPEG, GIF, or WEBP image under 5 MB.", "danger")
        return redirect(url_for("dashboard"))
    filename = save_image(uploaded)
    flash(f"Uploaded {filename}. Use that filename when editing a post.", "success")
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:sno>", methods=["POST"])
@admin_required
def delete(sno):
    db.session.delete(db.get_or_404(Post, sno))
    db.session.commit()
    flash("Post deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout", methods=["POST"])
@admin_required
def logout():
    session.clear()
    return redirect(url_for("auth"))


@app.errorhandler(413)
def file_too_large(_error):
    flash("File is too large. The limit is 5 MB.", "danger")
    return redirect(url_for("dashboard"))


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_ENV") != "production")
