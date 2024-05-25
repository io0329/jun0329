from flask import Flask,redirect,url_for,render_template,request,session, flash

app = Flask(__name__)



@app.route("/")
def home():
    return render_template("desk.html")

@app.route("/login", methods=["POST","GET"])
def login():
    if request.method=="POST":
        session.permanent=True #애플리케이션에서 세션을 영구적으로 유지하도록 지정, 영구적인 세션을 사용할 때는 세션 쿠키의 만료 시간을 설정해야 합니다
        username=request.form["ID"]
        pw=request.form["PW"]
        session["user"]=username
        return render_template("login.html")

@app.route("/join")
def join():
        return render_template("join.html")
    

@app.route("/write")
def write():
        return render_template("write.html")


if __name__=="__main__":
    app.run(debug=True)