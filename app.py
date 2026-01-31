from flask import Flask, render_template, request, redirect, session ,jsonify
from auth.signup import signup_user
from database.client import supabase
from datetime import *

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
    session['theme']=profile.data["theme"]

    supabase.table("user_profiles") \
        .update({"status": True}) \
        .eq("id", user_id) \
        .execute()

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
    supabase.table("user_profiles") \
        .update({"status": False}) \
        .eq("id", session['id']) \
        .execute()
    session.clear()
    return redirect("/login")

@app.route("/search", methods=["GET", "POST"])
def search():
    query=request.args.get("q")


    users = supabase.table("users") \
    .select("*, user_profiles(profile_pic, bio)") \
    .ilike("username", f"%{query}%") \
    .neq("username", session['user']) \
    .execute()

    return jsonify(users.data)

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

@app.route("/chat/<username>")
def chat(username):
    user_id = supabase.table("users") \
    .select("id") \
    .eq("username", username) \
    .execute()
    user_id=user_id.data[0]['id']
    
    chat_user = supabase.table("user_profiles") \
    .select("*") \
    .eq("id", user_id) \
    .execute()
    print(chat_user.data)
    user_pfp=chat_user.data[0]['profile_pic']
    user_status=chat_user.data[0]['status']

    return(render_template("chat.html",user_name=username,user_pfp=user_pfp,user_status=user_status,theme=session['theme']))

@app.route("/send_message",methods=["GET"])
def SendMessage():
    msg = request.args.get("msg")
    receiver = request.args.get("receiver")
    lastView=request.args.get('lastView')

    supabase.table("messages").insert({
    "sender": session["user"],
    "receiver": receiver,
    "image_url": msg,
    "lastView":lastView
    }).execute()

    # me = session["user"]
    # messages = supabase.table("messages") \
    # .select("*") \
    # .or_(
    #     f"and(sender.eq.{me},receiver.eq.{receiver}),"
    #     f"and(sender.eq.{receiver},receiver.eq.{me})"
    # ) \
    # .order("time", desc=False) \
    # .execute()
    # messages=messages.data
    return jsonify({"status":"ok"})

@app.route('/get_messages')
def getMessages():
    receiver = request.args.get("receiver")
    me = session["user"]
    timestamp = request.args.get("timestamp")
    


    if timestamp and timestamp!="null":
        messages = supabase.table("messages") \
        .select("*") \
        .or_(
            f"and(sender.eq.{me},receiver.eq.{receiver}),"
            f"and(sender.eq.{receiver},receiver.eq.{me})"
        ) \
        .order("time", desc=False) \
        .gt("time", timestamp) \
        .execute()
    else:
        messages = supabase.table("messages") \
        .select("*") \
        .or_(
            f"and(sender.eq.{me},receiver.eq.{receiver}),"
            f"and(sender.eq.{receiver},receiver.eq.{me})"
        ) \
        .order("time", desc=False) \
        .execute()

    print(messages.data )
    messages=messages.data
    return jsonify(messages)

@app.route('/recent_chats')
def RecentChats():
    me = session["user"]
    recentchats = supabase.table('messages')\
    .select("*") \
    .or_(
        f"and(sender.eq.{me}),"
        f"and(receiver.eq.{me})"
    ) \
    .order("time", desc=False) \
    .execute()
    print(recentchats.data)
    chats=[]
    for i in recentchats.data:
        if(i['sender'] in chats):
            chats.remove(i['sender'])
            chats.insert(0,i['sender'])
        elif(i['receiver'] in chats):
            chats.remove(i['receiver'])
            chats.insert(0,i['receiver'])
        else:
            if(i['sender']==session['user']):
                chats.insert(0,i['receiver'])
            else:
                chats.insert(0,i['sender'])
    print(chats)
    return jsonify(chats)

@app.route('/fetch_profile')
def fetchProfile():
    name = request.args.get("name")
    users = supabase.table("users") \
    .select("user_profiles(profile_pic)") \
    .eq("username",name)\
    .single()\
    .execute()
    print(users.data)
    pfp = users.data['user_profiles']
    return jsonify(pfp['profile_pic'])


if __name__ == "__main__":
    app.run(debug=True)