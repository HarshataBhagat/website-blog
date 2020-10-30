from flask import Flask, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
from flask_mail import Mail
import math
import json
import os
from datetime import datetime


with open('config.json','r') as c:
    para = json.load(c) ["para"] 

local_server = True
app = Flask(__name__)
app.secret_key = 'thisismysecretkeydonotstealitokay'
app.config['UPLOAD_FOLDER'] = para['upload_location']
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = para['gmail-user'],
    MAIL_PASSWORD = para['gmail-password'],
))
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = para['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = para['prod_uri']

db = SQLAlchemy(app)

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    subtitle = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String(100), nullable=False)
    postby = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    slug = db.Column(db.String(21), nullable=False)
    img_file = db.Column(db.String(21), nullable=True)


@app.route('/')
def index():
    posts = Posts.query.filter_by().all() 
    last = math.ceil(len(posts)/int(para['no_of_posts']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(para['no_of_posts']): (page-1)*int(para['no_of_posts']) + int(para['no_of_posts'])]
    if(page==1):
        prev = '#'
        next ='/?page=' + str(page + 1)
    elif(page==last):
        prev = '/?page=' + str(page - 1)
        next = '#'    
    else:
        prev = '/?page=' + str(page - 1)
        next ='/?page=' + str(page + 1)
    
    return render_template('index.html', para=para, posts=posts, prev=prev, next=next)

@app.route('/about')
def about():
    return render_template('about.html', para=para)

@app.route('/dashboard', methods=['POST','GET'])
def dashboard():

    if ('user' in session and session['user'] == para['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html',para=para, posts=posts)

    if request.method == 'POST':
        username=request.form.get('uname')
        userpass=request.form.get('password')
        if (username == para['admin_user'] and userpass == para['admin_password']):
            session['user']=username
            posts = Posts.query.all()
            return render_template('dashboard.html',para=para, posts=posts)
    return render_template('login.html',para=para)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', para=para, post=post)





@app.route('/edit/<string:sno>', methods = ['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == para['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            content = request.form.get('content')
            postby = request.form.get('postby')
            slug = request.form.get('slug')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno=='0':
                post = Posts(title=box_title, subtitle=subtitle, content=content, postby=postby, date=date, slug=slug, img_file=img_file)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.subtitle = subtitle
                post.content = content
                post.postby = postby
                post.slug = slug
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+ sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', para=para, sno=sno, post=post)                

@app.route('/uploader', methods=['GET','POST'])
def uploader():
     if ('user' in session and session['user'] == para['admin_user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully!"

@app.route("/delete/<string:sno>", methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == para['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/contact', methods=['GET','POST'])
def contact():
    if (request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        msg = request.form.get('msg')
        add = Contact(name=name, email=email, phone=phone, msg=msg, date=datetime.now() )
        db.session.add(add)
        db.session.commit()
        mail.send_message('New message from' +" " +  name,
                          sender=email,
                          recipients = [para['gmail-user']],
                          body= msg+ "\n" + phone
                          )
    return render_template('contact.html', para=para)

if __name__ == '__main__':
    app.run(debug=True)

    
