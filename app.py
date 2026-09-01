from flask import Flask,render_template,request,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json


with open('cofig.json', 'r') as c:
      paras=json.load(c)["para"]

app= Flask(__name__)
app.secret_key='super-secret-key'
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

        return render_template("edit.html",paras=paras,sno=sno)



@app.route("/")
def home():
    post=Post.query.filter_by().all()[0:paras['no_of_posts']]
    return  render_template ("index.html",post=post,paras=paras)



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
app.run(debug=True) 