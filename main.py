from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from flask_mail import Mail
import json
from datetime import datetime

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']

)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    '''
S.no., name, Phone.no, message, elmail, date
    '''
    Sno= db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.String(20), nullable=False)
    Phone_num = db.Column(db.String(12), nullable=False)
    Message = db.Column(db.String(120),  nullable=False)
    Date = db.Column(db.String(12), nullable=True)

class Posts(db.Model):
    Sno= db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    Content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    return render_template('index.html', params=params,posts=posts)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html', params=params, post=post)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts = posts)


    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username== params['admin_user'] and userpass== params['admin_password']):
            #set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts = posts)
    else:
        return render_template('login.html', params=params)

@app.route("/edit/<string:Sno>", methods = ['GET', 'POST'])
def edit(Sno):
    if('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if Sno == '0':
                post = Posts(Title=box_title, slug = slug, Content=content, tagline=tline, img_file=img_file, Date = date)
                db.session.add(post)
                db.session.commit()
                return redirect('/dashboard')

            else:
                post=Posts.query.filter_by(Sno=Sno).first()
                post.Title = box_title
                post.tagline=tline
                post.slug=slug
                post.Content=content
                post.img_file=img_file
                post.Date=date
                db.session.commit()
                return redirect(url_for('/edit/'+Sno))
        post = Posts.query.filter_by(Sno=Sno).first()

        return render_template('edit.html', params=params, post=post)

@app.route("/editing/<string:Sno>", methods = ['GET', 'POST'])
def editing(Sno):
    if "user" in session and session["user"] == params["admin_user"]:
        if request.method == 'POST':
            title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            if Sno=='0':
                post = Posts(Title=title, slug=slug, Content=content, tagline=tline, img_file=img_file, Date=date)
                db.session.add(post)
                db.session.commit()
                return redirect('/dashboard')
            else:
                post = Posts.query.filter_by(Sno=Sno).first()
                post.Title = title
                post.slug = slug
                post.Content = content
                post.tagline = tline
                post.img_file = img_file
                post.Date = date
                db.session.commit()
                return redirect('/dashboard')
        post = Posts.query.filter_by(Sno=Sno).first()
        return render_template('editing.html',params=params,post = post,Sno=Sno)
    else:
        return render_template("login.html", params=params)

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/delete/<string:Sno>", methods = ['GET', 'POST'])
def delete(Sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(Sno=Sno)
        db.session.delete(post).first()
        db.session.commit()
    return redirect('/dashboard')

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method == 'POST'):
        '''Add entry to the database '''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(Name=name, Phone_num=phone, Message=message, Date= datetime.now(), Email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender =email,
                          recipients = [params['gmail_user']],
                          body = message + "\n" + phone
                          )



    return render_template('contact.html', params=params)


app.run(debug=True)
