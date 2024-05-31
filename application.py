from flask import Flask,redirect,url_for,render_template,request,session, flash
import pymysql
from datetime import timedelta
app = Flask(__name__)
app.secret_key = "hello"
app.permanent_session_lifetime = timedelta(days=5) 

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
            elif search_option == 'option2':  # 제목 검색
                cursor.execute("SELECT * FROM board WHERE title LIKE %s ORDER BY date DESC", ('%' + search_query + '%',))
            elif search_option == 'option3':  # 내용 검색
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
        cursor.execute("SELECT * FROM board where idx = %s ORDER BY date DESC", idx)
        posts = cursor.fetchall()
        
    connection.close()
    return render_template("view.html", posts=posts)



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

        if pw == checkpw:
            try:
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    sql = "INSERT INTO members (id, password, name, email) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (id, pw, name, email))
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
        file = request.form["file"]
        secret = request.form.get("secret", "n")  # 기본값은 "n"
        
        writer_id = session.get("user")  # 세션에서 로그인된 사용자의 ID를 가져옴

        if writer_id:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # 멤버 테이블에서 ID와 이름을 가져옴
                cursor.execute("SELECT id, name FROM members WHERE id = %s", (writer_id,))
                member = cursor.fetchone()
                if member:
                    writer_name = member["name"]
                    sql = "INSERT INTO board (title, content, id, writer, password, file, secret, date) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"
                    cursor.execute(sql, (title, content, writer_id, writer_name, password, file, secret))
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
    if request.method=='POST':
        password=request.form["password"]
        idx= request.form["idx"]
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT password FROM board WHERE idx=%s", (idx))
            member = cursor.fetchone()
            if member:
                if member["password"] == password:
                    cursor.execute("DELETE FROM board WHERE idx=%s", (idx))
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
        file = request.form["file"]
        secret = request.form.get("secret", "n") 
        idx = request.form["idx"]

        if idx:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                sql = "update board set title=%s, password=%s, content=%s, file=%s, secret=%s WHERE idx = %s"
                cursor.execute(sql, (title, password, content, file, secret,idx))
                connection.commit()
            connection.close()
            return redirect(url_for("home"))

    return render_template("modify.html")




if __name__=="__main__":
    app.run(debug=True)
