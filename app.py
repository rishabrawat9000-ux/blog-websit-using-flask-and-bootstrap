from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
with open('cofig.json', 'r') as c:
      paras=json.load(c)["para"]

app= Flask(__name__)
app.secret_key='super-secret-key'
app.config['UPLOAD_FOLDER'] = paras['loccaton']
app.config['SQLALCHEMY_DATABASE_URI'] = paras['local_uri'] if paras['local_server']=="TRUE"else paras["prod_uri"]
db=SQLAlchemy(app)
app.config.update(
   mail_server="smtp.gmail.com",
   mail_port='587',
   mail_use_tls=True,
   mail_username=paras['email'],
   mail_password=paras['gmail-password']
)
class Post(db.Model):
    sno=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(800),nullable=False)
    author=db.Column(db.String(800),nullable=False)
    slug=db.Column(db.String(800),nullable=False)
    content=db.Column(db.String(1200),nullable=False)
    date=db.Column(db.DateTime,nullable=False)
    img_file=db.Column(db.String(120),nullable=False)

class Contact(db.Model):
      sno=db.Column(db.Integer,primary_key=True)
      name=db.Column(db.String(800),nullable=False)
      email=db.Column(db.String(8000),nullable=False)
      phone=db.Column(db.Integer,nullable=False)
      msg=db.Column(db.String(200),nullable=False)
      date=db.Column(db.DateTime,nullable=False)

@app.context_processor
def inject_paras():
    return dict(paras=paras)

@app.route("/auth",methods=['GET','POST'])
def auth():
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        if('user' in session and session['user']==paras['user_name']):
            post=Post.query.all()
            return render_template("dashboard.html",paras=paras,post=post)

        elif (username==paras["user_name"]) and (password==paras["password"]):
            post=Post.query.all()
            session['user']=username
            return render_template("dashboard.html",paras=paras,post=post)
        else:
            return render_template("auth.html",paras=paras,error="Invalid username or password!")
    else:
        return render_template ("auth.html",paras=paras)


@app.route("/edit/<sno>",methods =["GET","POST"])
def edit(sno):
    if ('user' in session and session["user"] == paras["user_name"]):
        if request.method == "POST":
            box_title = request.form.get("title")
            box_slug = request.form.get("slug")
            box_content = request.form.get("content")
            box_author = request.form.get("author")
            box_img = request.form.get("img_file")



            if(sno=='0'):
                post1=Post(title=box_title,slug=box_slug,content=box_content,author=box_author,img_file=box_img,date=datetime.now())
                db.session.add(post1)
                db.session.commit()
            else:
                post=Post.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = box_slug
                post.content = box_content
                post.author= box_author
                post.img_file = box_img
                db.session.commit()
                
                return  redirect("/edit/"+sno)
        post=Post.query.filter_by(sno=sno).first()    
        return render_template("edit.html",paras=paras,post=post)


@app.route("/")
def home():
    per_page = int(paras['no_of_posts'])

    page = request.args.get('page', 1)

    if not str(page).isnumeric():
        page = 1

    page = int(page)

    posts = Post.query.all()

    last = (len(posts) + per_page - 1) // per_page

    if last == 0:
        last = 1

    # Loop back to page 1 after the last page
    if page > last:
        page = 1

    if page < 1:
        page = 1

    posts = posts[
        (page - 1) * per_page:
        page * per_page
    ]

    # Next page
    if page == last:
        next = 1
    else:
        next = page + 1

    return render_template(
        "index.html",
        post=posts,
        paras=paras,
        next=next,
        page=page,
        last=last
    )



@app.route("/about")
def about():
    return render_template ("about.html")



@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        msg = request.form.get('message')
        email = request.form.get('email')

        entry = Contact(
            name=name,
            email=email,
            phone=phone,
            msg=msg,
            date=datetime.now()
        )

        db.session.add(entry)
        db.session.commit()
        
    return render_template("contact.html")


@app.route("/post/<post_slug>")
def post(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template("post.html", post=post, paras=paras)


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session["user"] == paras["user_name"]):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully"
    else:
        return redirect("/auth")
@app.route("/delete/<sno>",methods =["GET","POST"])
def delete(sno):
    if ('user' in session and session["user"] == paras["user_name"]):
        post=Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/auth")
@app.route("/logout")
def logout():
    session.pop('user',None)
    return redirect("/auth")


app.run(debug=True) 
