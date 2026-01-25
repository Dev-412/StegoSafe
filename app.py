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

        exists = supabase.table("users").select("id").eq("username", username).execute()
        

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
    username = session["user"]

    user = supabase.table("users") \
    .select("id") \
    .eq("username", username) \
    .single() \
    .execute()

    user_id = user.data["id"]
    session['id']=user_id

    profile = supabase.table("user_profiles") \
    .select("*") \
    .eq("id", user_id) \
    .single() \
    .execute()

    pfp = profile.data["profile_pic"]

    session["pfp"]=pfp

    # return render_template(
    # "dashboard.html",
    # username=username,
    # pfp=pfp,
    # theme=profile.data["theme"],
    # recent_chats=recent_chats,
    # users=users)

    return render_template("dashboard.html",username=username,pfp=pfp,theme=profile.data["theme"])

@app.route("/profile", methods=["GET", "POST"])
def profile():
    pfp = session['pfp']
    user_id = session['id']
    profile = supabase.table("user_profiles") \
    .select("*") \
    .eq("id", user_id) \
    .single() \
    .execute()

    bio = profile.data['bio']
    theme = profile.data['theme']
    return render_template("profile.html",pfp=pfp,bio=bio,theme=theme)


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

@app.route("/upload-avatar", methods=["POST"])
def upload_avatar():
    file = request.files.get("avatar")

    if not file or file.filename == "":
        return redirect("/profile")

    user_id = session.get("id")
    if not user_id:
        return redirect("/login")

    path = f"avatars/{user_id}/avatar.png"

    # upload to storage
    supabase.storage.from_("avatars").upload(
        path,
        file.read(),
        {
            "content-type": file.content_type,
            "upsert": "true"
        }
    )

    # get public URL
    public_url = supabase.storage.from_("avatars").get_public_url(path)

    # update table
    supabase.table("user_profiles") \
        .update({"profile_pic": public_url}) \
        .eq("id", user_id) \
        .execute()
    
    session['pfp']=public_url

    return redirect("/profile")

@app.route("/update-profile", methods=["POST"])
def update_profile():

    # must be logged in
    user_id = session.get("id")
    if not user_id:
        return redirect("/login")

    # get form values
    bio = request.form.get("bio")
    theme = request.form.get("theme")

    # update database
    supabase.table("user_profiles") \
        .update({
            "bio": bio,
            "theme": theme
        }) \
        .eq("id", user_id) \
        .execute()

    # update session for immediate effect
    session["theme"] = theme
    session["bio"] = bio

    return redirect("/profile")

@app.route("/chat/{{ user.username }}")
def chat():
    return("HEllo")


if __name__ == "__main__":
    app.run(debug=True)