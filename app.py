from flask import Flask, render_template, request, redirect, session
from auth.signup import signup_user
from database.client import supabase

app = Flask(__name__)
app.secret_key = "STEGOSAFE_SECRET"  


@app.route("/")
def home():
    return redirect("/login")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        cpassword = request.form["cpassword"]

        exists = supabase.table("users") \
            .select("id") \
            .eq("username", username) \
            .execute()
        

        if exists.data:
            return render_template("signup.html", error="Username already exists")
        elif password != cpassword:
            return render_template("signup.html", error="Passwords do not match")
        elif( len(password)<8):
            return render_template("signup.html", error="Password Should be of 8 Digits or Greater..")
        else:
            signup_user(username, password, cpassword)
            session["user"] = username
            return redirect("/dashboard")
        
    return render_template("signup.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        result = supabase.table("users").select("*").eq("username", username).execute()

        if not result.data:
            return render_template("login.html", error="No User Found")
        elif (result.data[0]["password"]!=password):
            return render_template("login.html", error="Invalid Password")
        else:
            session["user"] = username
            return redirect("/dashboard")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form["search"]

    users = supabase.table("users") \
    .select("username") \
    .ilike("username", f"%{query}%") \
    .execute()
    return render_template("dashboard.html",users=users.data)

@app.route("/chat/{{ user.username }}")
def chat():
    return("HEllo")


if __name__ == "__main__":
    app.run(debug=True)
