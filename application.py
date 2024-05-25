from flask import Flask,redirect,url_for,render_template,request,session, flash

app = Flask(__name__)



@app.route("/")
def home():
    return render_template("desk.html")

@app.route("/login", methods=["POST","GET"])
def login():
    if request.method=="POST":
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
