from flask import Flask, redirect, url_for, render_template, request, session, flash, send_from_directory
import pymysql
from datetime import timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "hello"
app.permanent_session_lifetime = timedelta(days=5)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024


def get_db_connection():
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='0647133079',
        db='lee',
        port=3307,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

@app.route("/", methods=["POST", "GET"])
def home():
    connection = get_db_connection()
    if request.method == "POST":
        search_option = request.form.get('options')
        search_query = request.form.get('query')
        with connection.cursor() as cursor:
            if search_option == 'option1':
                cursor.execute("SELECT * FROM board WHERE title LIKE %s OR content LIKE %s ORDER BY date DESC", ('%' + search_query + '%', '%' + search_query + '%'))
            elif search_option == 'option2':
                cursor.execute("SELECT * FROM board WHERE title LIKE %s ORDER BY date DESC", ('%' + search_query + '%',))
            elif search_option == 'option3':
                cursor.execute("SELECT * FROM board WHERE content LIKE %s ORDER BY date DESC", ('%' + search_query + '%',))
            posts = cursor.fetchall()
    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM board ORDER BY date DESC")
            posts = cursor.fetchall()

    connection.close()
    return render_template("desk.html", posts=posts)

@app.route("/view/<int:idx>")
def view(idx):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM board WHERE idx = %s", (idx,))
        post = cursor.fetchone()
        
    connection.close()
    
    if post:
        if post["secret"] == "on":
            return redirect(url_for("checkup", idx=idx))
        else:
            return render_template("view.html", posts=[post])
    else:
        flash("게시물을 찾을 수 없습니다.")
        return redirect(url_for("home"))

@app.route("/checkup", methods=["GET", "POST"])
def checkup():
    if request.method == "POST":
        idx = request.form.get("idx")
        password = request.form.get("password")
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM board WHERE idx = %s", (idx,))
            post = cursor.fetchone()
        
        connection.close()
        
        if post and post["password"] == password:
            return render_template("view.html", posts=[post])
        else:
            flash("비밀번호가 일치하지 않습니다.")
            return redirect(url_for("checkup", idx=idx))

    idx = request.args.get("idx")
    return render_template("checkup.html", idx=idx)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["id"]
        pw = request.form["pw"]

        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM members WHERE id = %s AND password = %s"
            cursor.execute(sql, (username, pw))
            user = cursor.fetchone()
        connection.close()

        if user:
            session["user"] = username
            return redirect(url_for("home"))
        else:
            flash('아이디 또는 패스워드가 잘못되었습니다.')
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == 'POST':
        id = request.form["id"]
        pw = request.form["pw"]
        checkpw = request.form["checkpw"]
        name = request.form["name"]
        email = request.form["email"]
        school = request.form["school"]

        if pw == checkpw:
            try:
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    sql = "INSERT INTO members (id, password, name, email, school) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql, (id, pw, name, email, school))
                    connection.commit()
                flash('회원가입이 성공적으로 완료되었습니다.', 'success')
            except Exception as e:
                flash('회원가입 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
                print(e)
            finally:
                connection.close()
            return redirect(url_for('login'))
        else:
            flash('비밀번호가 일치하지 않습니다.', 'error')

    return render_template("join.html")

@app.route("/write", methods=["GET", "POST"])
def write():
    if request.method == 'POST':
        title = request.form["title"]
        password = request.form["password"]
        content = request.form["content"]
        secret = request.form.get("secret", "n")

        file = request.files["file"]
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        else:
            filename = None

        writer_id = session.get("user")

        if writer_id:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, name FROM members WHERE id = %s", (writer_id,))
                member = cursor.fetchone()
                if member:
                    writer_name = member["name"]
                    sql = "INSERT INTO board (title, content, id, writer, password, file, secret, date) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"
                    cursor.execute(sql, (title, content, writer_id, writer_name, password, filename, secret))
                    connection.commit()
                else:
                    flash("멤버를 찾을 수 없습니다.", "error")
                    return redirect(url_for("login"))
            connection.close()
            return redirect(url_for("home"))
        else:
            flash("로그인이 필요합니다.", "error")
            return redirect(url_for("login"))
    return render_template("write.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/delete", methods=["GET", "POST"])
def delete():
    if request.method == 'POST':
        password = request.form["password"]
        idx = request.form["idx"]
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT password FROM board WHERE idx = %s", (idx,))
            member = cursor.fetchone()
            if member:
                if member["password"] == password:
                    cursor.execute("DELETE FROM board WHERE idx = %s", (idx,))
                    connection.commit()
                    connection.close()
                    return redirect(url_for("home"))
                else:
                    flash("비밀번호가 일치하지 않습니다.")
                    connection.close()
                    return redirect(url_for("delete", idx=idx))
            else:
                flash("게시물을 찾을 수 없습니다.")
                connection.close()
                return redirect(url_for("home"))

    return render_template("delete.html")

@app.route("/modify", methods=["GET", "POST"])
def modify():
    if request.method == 'POST':
        title = request.form["title"]
        password = request.form["password"]
        content = request.form["content"]
        secret = request.form.get("secret", "n")
        idx = request.form["idx"]

        file = request.files["file"]
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        else:
            filename = request.form.get("existing_file")

        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "UPDATE board SET title=%s, password=%s, content=%s, file=%s, secret=%s WHERE idx=%s"
            cursor.execute(sql, (title, password, content, filename, secret, idx))
            connection.commit()
        connection.close()
        return redirect(url_for("home"))
    
    idx = request.args.get("idx")
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM board WHERE idx = %s", (idx,))
        post = cursor.fetchone()
    connection.close()
    return render_template("modify.html", post=post)


@app.route("/find_id", methods=["GET", "POST"])
def find_id():
    if request.method == "POST":
        email = request.form["email"]
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM members WHERE email = %s", (email,))
            user = cursor.fetchone()
        connection.close()
        if user:
            flash(f"아이디는 {user['id']} 입니다.", "success")
        else:
            flash("해당 이메일로 등록된 사용자가 없습니다.", "error")
        return redirect(url_for("find_id"))
    return render_template("find_id.html")

@app.route("/find_password", methods=["GET", "POST"])
def find_password():
    if request.method == "POST":
        id = request.form["id"]
        email = request.form["email"]

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM members WHERE id = %s AND email = %s", (id, email))
            user = cursor.fetchone()

        if user:
            flash(f"비밀번호는 {user['password']} 입니다.", "success")
        else:
            flash("해당 이메일로 등록된 사용자가 없습니다.", "error")

    return render_template("find_password.html")

@app.route("/myprofile")
def myprofile():
    if "user" in session:
        username = session["user"]
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM members WHERE id = %s", (username,))
            user = cursor.fetchone()
        connection.close()

        if user:
            return render_template("myprofile.html", user=user)
        else:
            flash("사용자 정보를 찾을 수 없습니다.", "error")
            return redirect(url_for("home"))
    else:
        flash("로그인이 필요합니다.", "error")
        return redirect(url_for("login"))

@app.route("/profile")
def profile():
    connection = get_db_connection()

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM members ORDER BY name DESC")
        posts = cursor.fetchall()

    connection.close()
    return render_template("profile.html", posts=posts)

@app.route("/showprofile/<string:username>")
def showprofile(username):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM members WHERE id = %s", (username,))
        user = cursor.fetchone()
    connection.close()

    if user:
        return render_template("showprofile.html", user=user)
    else:
        flash("사용자 정보를 찾을 수 없습니다.", "error")
        return redirect(url_for("profile"))

@app.route("/mymodify", methods=["GET", "POST"])
def mymodify():
    if "user" not in session:
        flash("로그인이 필요합니다.", "error")
        return redirect(url_for("login"))

    username = session["user"]
    connection = get_db_connection()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        school = request.form["school"]
        pw = request.form["pw"]

        with connection.cursor() as cursor:
            if pw:
                sql = "UPDATE members SET name = %s, email = %s, school = %s, password = %s WHERE id = %s"
                cursor.execute(sql, (name, email, school, pw, username))
            else:
                sql = "UPDATE members SET name = %s, email = %s, school = %s WHERE id = %s"
                cursor.execute(sql, (name, email, school, username))
            connection.commit()
        return redirect(url_for("profile"))
    else:
        return render_template("mymodify.html")
    
    
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    app.run(debug=True)
