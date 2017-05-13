#!/usr/bin/python3
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_mysqldb import MySQL
import hashlib
import os , base64
# init

app = Flask(__name__)
app.secret_key = "E5CDD5E9422A8D509A392DB9621097C2DEFF1C1AE90714A78AC84E3EAC072E87" #remember to change it!
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'pass'
app.config['MYSQL_DB'] = 'FLASK_FORUM'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)
# ---

#Functions
def hashPassword(password, salt):
    tempPasswordHash = hashlib.sha512(password.encode("UTF-8")).hexdigest()
    return hashlib.sha256((tempPasswordHash + salt).encode("UTF-8")).hexdigest()
#---

@app.route("/")
def index():
    return render_template("index.html", p=1)

#Forum
@app.route("/forum/<page>")
def forum(page):
    page = int(page)
    cur = mysql.connection.cursor()
    limit = 30
    offset = limit*page
    nextPageExists = False
    pinned = {}
    if page == 0:
        cur.execute('''
            SELECT TOPICS.ID, TOPICS.NAME, USERS.USERNAME AS 'CREATOR', Count(POSTS.ID) AS 'POSTS', MAX(POSTS.CREATION_DATE) AS 'LASTPOST'
            FROM TOPICS
            INNER JOIN USERS ON TOPICS.CREATORID = USERS.ID
            LEFT JOIN POSTS ON POSTS.TOPICID = TOPICS.ID
            WHERE TOPICS.ISPINNED = TRUE
            GROUP BY TOPICS.ID
            ORDER BY LASTPOST DESC;''')
        pinned = cur.fetchall()
    cur.execute('''
        SELECT TOPICS.ID, TOPICS.NAME, USERS.USERNAME AS 'CREATOR', Count(POSTS.ID) AS 'POSTS', MAX(POSTS.CREATION_DATE) AS 'LASTPOST'
        FROM TOPICS
        INNER JOIN USERS ON TOPICS.CREATORID = USERS.ID
        LEFT JOIN POSTS ON POSTS.TOPICID = TOPICS.ID
        WHERE TOPICS.ISPINNED = FALSE
        GROUP BY TOPICS.ID
        ORDER BY LASTPOST DESC
        LIMIT %s, %s''', (offset,limit+1,))
    topics = cur.fetchall()

    if len(topics) > limit:
        nextPageExists = True
    topics = topics[:limit]

    if len(topics) == 0 and page != 0:
        return redirect("/forum/"+str(page-1))

    return render_template("forum.html", p=2, topics=topics, pinned=pinned, page = page, nextPageExists = nextPageExists)

@app.route("/forum/topic/<forumPage>/<topicID>/<page>")
def topic(forumPage, topicID, page):
    page = int(page)
    limit = 10
    nextPageExists = False
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT TOPICS.NAME
        FROM TOPICS
        WHERE TOPICS.ID = %s;''', (topicID, ))
    name = cur.fetchone()['NAME']
    cur.execute('''
        SELECT POSTS.CONTENT, POSTS.CREATION_DATE, USERS.USERNAME, USERS.ISADMIN
        FROM POSTS
        INNER JOIN USERS ON POSTS.CREATORID = USERS.ID
        WHERE POSTS.TOPICID = %s
        ORDER BY POSTS.CREATION_DATE
        LIMIT %s, %s;''', (topicID, page*limit, limit+1))
    posts = cur.fetchall()
    if len(posts) > limit:
        nextPageExists = True
    if len(posts) == 0 and page != 0:
        return redirect("/forum/topic/"+forumPage+"/"+topicID+"/"+str(page-1))
    posts = posts[:limit]
    return render_template("topic.html", p=2, posts = posts, name = name, topicID = topicID, forumPage = forumPage, page = page, nextPageExists = nextPageExists)

#Create post, topic

def createPostFunction(content, topicID, userID):
    cur = mysql.connection.cursor()
    cur.execute('''
        INSERT INTO POSTS(CONTENT, CREATORID, TOPICID)
        VALUE (%s, %s, %s)
        ''', (content, userID, topicID))
    mysql.connection.commit()
    cur.close()
    return

@app.route("/forum/createPost", methods=['POST'])
def createPost():
    content = request.form['content']
    topicID = request.form['topicID']
    page = request.form['page']
    if not session.get('logged_in'):
        flash(u"You must be logged in!", "danger")
    elif not content:
        flash(u"Post must contain content!", "danger")
    else:
        userID = session.get('ID')
        createPostFunction(content, topicID, userID)
    return redirect("/forum/topic/0/"+topicID+"/"+page)

@app.route("/forum/createTopic", methods=['POST'])
def createTopic():
    content = request.form['content']
    title = request.form['title']
    userID = session.get('logged_in')
    if not userID or not session.get('logged_in'):
        flash(u"You must be logged in!", "danger")
    elif not content or not title:
        flash(u"Topic must contain content and title!", "danger")
    else:
        cur = mysql.connection.cursor()
        cur.execute('''
            INSERT INTO TOPICS(NAME, CREATORID)
            VALUE (%s, %s)
            ''', (title, userID))
        mysql.connection.commit()
        topicID = cur.lastrowid
        cur.close()
        createPostFunction(content, topicID, userID)
        return redirect("/forum/topic/0/"+str(topicID)+"/0")
    return redirect("/forum")
# ---

#Panel
@app.route("/panel")
def panel():
    if session.get('logged_in') == True:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM USERS WHERE USERNAME = %s", (session['username'],))
        return render_template("panel.html", p=3, user=cur.fetchone())
    return render_template("login.html", p=3)
# ---

#Login / Register / Logout scripts
@app.route("/login", methods=['POST'])
def login():
    _username = request.form['username']
    _passwd = request.form['passwd']

    cur = mysql.connection.cursor()
    res = cur.execute("SELECT * FROM USERS WHERE USERNAME = %s", (_username,))

    if res > 0:
        user = cur.fetchone()
        hashedPass = hashPassword(_passwd, user['SALT'])
        if(hashedPass == user['PASSWORD_HASH']):
            session['ID'] = user['ID']
            session['username'] = user['USERNAME']
            session['logged_in'] = True
            flash(u"You're now logged in!", "info")
        else:
            flash(u"Passwords don't match!", "danger")
    else:
        flash(u"Incorrect login", "danger")
    return redirect(url_for('panel'))

@app.route("/register", methods=['POST'])
def register():
    _username = request.form['username']
    _passwd = request.form['passwd']
    _passwdcheck = request.form['passwdcheck']
    _email = request.form['email']

    if len(_username) < 2 or len(_username) > 20:
        flash(u"Incorrect username lenght!", "danger")
        return redirect(url_for('panel'))

    if _passwd != _passwdcheck:
        flash(u"Passwords don't match!", "danger")
        return redirect(url_for('panel'))

    cur = mysql.connection.cursor()
    res = cur.execute("SELECT * FROM USERS WHERE USERNAME = %s OR EMAIL = %s", (_username, _email))

    if res != 0:
        flash(u"User exists!", "danger")
        return redirect(url_for('panel'))

    salt = base64.b64encode(os.urandom(16)).decode('utf-8')[:16]
    passwordHash = hashPassword(_passwd, salt)
    cur.execute("INSERT INTO USERS(USERNAME, EMAIL, PASSWORD_HASH, SALT) VALUES (%s, %s, %s, %s)", (_username, _email, passwordHash, salt))

    mysql.connection.commit()
    cur.close()
    flash(u"You're now registered!", "info")
    return redirect(url_for('panel'))

@app.route("/logout")
def logut():
    session.clear()
    return redirect(url_for('index'))
# ---

if __name__ == "__main__":
    app.run(host='', port=8080)
