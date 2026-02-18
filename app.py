from flask import Flask, render_template, request, redirect, session, jsonify, send_file, flash
from auth.signup import signup_user
from utils.email_sender import send_otp_email, send_password_success_email
import random
from auth.RSA import *
from database.client import supabase
from datetime import *
import json
from auth.carrier import get_random_image
from auth.Stego import hide_text_in_image
from auth.stego_toolkit import hide_file_in_image, reveal_file_from_image
from dotenv import load_dotenv
load_dotenv()
from io import BytesIO
import uuid
import os
import re


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") 


@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return render_template("landing.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        cpassword = request.form["cpassword"]

        exists = supabase.table("users").select("id").eq("username", username).execute()
        

        if exists.data:
            return render_template("signup.html", error="Username already exists")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return render_template("signup.html", error="Invalid Email Address")
        elif password != cpassword:
            return render_template("signup.html", error="Passwords do not match")
        elif( len(password)<8):
            return render_template("signup.html", error="Password Should be of 8 Digits or Greater..")
        else:
            res = signup_user(username, password, email)
            if res != "success":
                return render_template("signup.html", error=res)
            
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
    .select("*, user_profiles(profile_pic, bio, status)") \
    .ilike("username", f"%{query}%") \
    .neq("username", session['user']) \
    .execute()

    return jsonify(users.data)

@app.route("/upload-avatar", methods=["POST"])
def upload_avatar():
    file = request.files.get("avatar")

    if not file or file.filename == "":
        flash("No file selected", "error")
        return redirect("/profile")

    user_id = session.get("id")
    if not user_id:
        return redirect("/login")

    path = f"avatars/{user_id}/avatar.png"

    try:
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
        flash("Avatar updated successfully!", "success")

    except Exception as e:
        flash(f"Error uploading avatar: {str(e)}", "error")

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

    flash("Profile settings saved.", "success")
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

    public_key = supabase.table("users") \
    .select("public_key") \
    .eq("username", receiver) \
    .single() \
    .execute()

    public_key = public_key.data['public_key']
    public_key = json.loads(public_key)
    print(public_key)

    cipher = encrypt(msg,public_key)

    payload = ",".join(map(str, cipher))
    

    # 1️⃣ random carrier
    carrier = get_random_image(400, 400)

    # 2️⃣ hide cipher
    stego_img = hide_text_in_image(carrier, payload)

    # 3️⃣ convert to bytes
    buf = BytesIO()
    stego_img.save(buf, format="PNG")
    buf.seek(0)

    filename = f"{uuid.uuid4()}.png"

    # 4️⃣ upload to bucket
    supabase.storage.from_("stego-images").upload(
        filename,
        buf.getvalue(),
        {"content-type": "image/png"}
    )

    # 5️⃣ get public URL
    url = supabase.storage.from_("stego-images").get_public_url(filename)

    # 6️⃣ store in DB
    data = supabase.table("messages").insert({
        "sender": session["user"],
        "receiver": receiver,
        "image_url": url
    }).execute()

    # 7️⃣ auto-reveal for sender
    try:
        msg_id = data.data[0]['id']
        supabase.table("message_reveals").insert({
            "message_id": msg_id,
            "username": session["user"]
        }).execute()
    except Exception as e:
        print(f"Auto-reveal failed: {e}")

    return jsonify({"status":"ok"})

@app.route('/get_messages')
def getMessages():

    receiver = request.args.get("receiver")
    me = session["user"]
    timestamp = request.args.get("timestamp")

    if timestamp and timestamp != "null":
        res = supabase.table("messages") \
            .select("*") \
            .or_(
                f"and(sender.eq.{me},receiver.eq.{receiver}),"
                f"and(sender.eq.{receiver},receiver.eq.{me})"
            ) \
            .order("time", desc=False) \
            .gt("time", timestamp) \
            .execute()
    else:
        res = supabase.table("messages") \
            .select("*") \
            .or_(
                f"and(sender.eq.{me},receiver.eq.{receiver}),"
                f"and(sender.eq.{receiver},receiver.eq.{me})"
            ) \
            .order("time", desc=False) \
            .execute()

    messages = res.data

    output = []

    for m in messages:

        msg_id = m["id"]

        # 🔍 check reveal state
        revealed = supabase.table("message_reveals") \
            .select("id") \
            .eq("message_id", msg_id) \
            .eq("username", me) \
            .execute()

        is_revealed = bool(revealed.data)

        row = dict(m)

        if is_revealed:

            # decrypt again (server-side)
            receiver_user = m["receiver"]

            priv_res = supabase.table("users") \
                .select("private_key") \
                .eq("username", receiver_user) \
                .single() \
                .execute()

            priv = json.loads(priv_res.data["private_key"])

            from auth.Stego import reveal_text_from_url

            hidden = reveal_text_from_url(m["image_url"])
            cipher = list(map(int, hidden.split(",")))

            row["revealed"] = True
            row["text"] = decrypt(cipher, priv)

        else:
            row["revealed"] = False

        output.append(row)

    return jsonify(output)



@app.route("/reveal_message")
def revealMessage():

    msg_id = request.args.get("id")
    me = session["user"]

    # fetch message row
    row = supabase.table("messages") \
        .select("*") \
        .eq("id", msg_id) \
        .single() \
        .execute()

    row = row.data

    sender = row["sender"]
    receiver = row["receiver"]

    # only chat members can reveal
    if me != sender and me != receiver:
        return jsonify({"error": "unauthorized"}), 403

    # decide whose private key is needed
    # always receiver's private key
    target_user = receiver

    priv_res = supabase.table("users") \
        .select("private_key") \
        .eq("username", target_user) \
        .single() \
        .execute()

    priv = json.loads(priv_res.data["private_key"])

    from auth.Stego import reveal_text_from_url

    hidden = reveal_text_from_url(row["image_url"])

    cipher = list(map(int, hidden.split(",")))

    msg = decrypt(cipher, priv)

    try:
        supabase.table("message_reveals").insert({
        "message_id": msg_id,
        "username": me
        }).execute()
    except:
        pass   # already revealed


    return jsonify({"text": msg})



# [{'id': '6b5ad12d-aae8-4f5e-ae43-1520c740ee21', 'sender': 'd1', 'receiver': 'dev', 'image_url': '3352228,4763535,5497629', 'time': '2026-02-03T13:47:25.385175'}, {'id': '507f231a-5098-4884-a1cf-d4261ced84c0', 'sender': 'd1', 'receiver': 'dev', 'image_url': '4763535,5497629', 'time': '2026-02-03T13:47:44.464134'}]

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
    try:
        users = supabase.table("users") \
        .select("user_profiles(profile_pic, status)") \
        .eq("username",name)\
        .single()\
        .execute()
        
        if not users.data:
            raise Exception("User not found")
            
        profile_data = users.data['user_profiles']
        
        # Check if profile_data is None (user exists but no profile)
        if not profile_data:
             # Return default if profile missing
            return jsonify({
                "pfp": "https://qliexogopxzdabruzeqb.supabase.co/storage/v1/object/public/avatars/default/blank.png",
                "status": False
            })

        return jsonify({
            "pfp": profile_data.get('profile_pic', "https://qliexogopxzdabruzeqb.supabase.co/storage/v1/object/public/avatars/default/blank.png"),
            "status": profile_data.get('status', False)
        })
    except Exception as e:
        print(f"Error fetching profile for {name}: {e}")
        # Return default profile on any error to prevent dashboard crash
        return jsonify({
            "pfp": "https://qliexogopxzdabruzeqb.supabase.co/storage/v1/object/public/avatars/default/blank.png",
            "status": False
        })

@app.route("/unrevealed_counts")
def unrevealedCounts():

    me = session["user"]

    # get all messages where I'm sender or receiver
    msgs = supabase.table("messages") \
        .select("id, sender, receiver") \
        .or_(
            f"and(sender.eq.{me}),"
            f"and(receiver.eq.{me})"
        ) \
        .execute()

    msgs = msgs.data

    # get reveal rows for me
    revealed = supabase.table("message_reveals") \
        .select("message_id") \
        .eq("username", me) \
        .execute()

    revealed_ids = {r["message_id"] for r in revealed.data}

    counts = {}

    for m in msgs:

        other = m["sender"] if m["sender"] != me else m["receiver"]

        # unrevealed only
        if m["id"] not in revealed_ids:

            counts[other] = counts.get(other, 0) + 1

    return jsonify(counts)


@app.route("/tools/encrypt", methods=["GET", "POST"])
def tools_encrypt():

    if request.method == "GET":
        return render_template(
            "tool_encrypt.html",
            theme=session.get("theme", "default")
        )

    # ---------- POST ----------

    image = request.files.get("image")
    payload = request.files.get("payload")
    output_name = request.form.get("output_name")
    if not output_name:
        output_name = "stego.png"

    if not image or not payload:
        return "Missing file", 400

    os.makedirs("tmp", exist_ok=True)

    img_path = f"tmp/{uuid.uuid4()}_{image.filename}"
    file_path = f"tmp/{uuid.uuid4()}_{payload.filename}"
    out_path = f"tmp/{output_name}"

    image.save(img_path)
    payload.save(file_path)

    try:
        out_path = hide_file_in_image(img_path, file_path, out_path)

        return send_file(out_path, as_attachment=True)

    except Exception as e:
        return jsonify({
        "success": False,
        "error": str(e)
        }), 400



@app.route("/tools/decrypt", methods=["GET", "POST"])
def tools_decrypt():

    if request.method == "GET":
        return render_template(
            "tool_decrypt.html",
            theme=session.get("theme", "default")
        )

    # ---------- POST ----------

    image = request.files.get("image")

    if not image:
        return jsonify({
            "success": False,
            "error": "No image uploaded"
        }), 400

    os.makedirs("tmp", exist_ok=True)

    img_path = f"tmp/{uuid.uuid4()}_{image.filename}"
    image.save(img_path)

    try:
        filename, data = reveal_file_from_image(img_path)

        # try decode as text
        try:
            text = data.decode("utf-8")
            return jsonify({
                "success": True,
                "text": text,
                "filename": filename
            })

        except:
            return jsonify({
                "success": True,
                "binary": True,
                "filename": filename,
                "size": len(data)
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
    
@app.route("/change-password", methods=["POST"])
def change_password():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    current_pw = request.form.get("current_password")
    new_pw = request.form.get("new_password")

    # fetch stored password
    res = supabase.table("users") \
        .select("password") \
        .eq("username", username) \
        .single() \
        .execute()

    stored_pw = res.data["password"]

    # check current
    if current_pw != stored_pw:
        flash("Incorrect current password.", "error")
        return redirect("/profile")

    if len(new_pw) < 8:
        flash("New password must be at least 8 characters.", "error")
        return redirect("/profile")

    # update password
    supabase.table("users") \
        .update({"password": new_pw}) \
        .eq("username", username) \
        .execute()

    flash("Password changed successfully.", "success")
    return redirect("/profile")


@app.route("/delete-account", methods=["POST"])
def delete_account():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]
    user_id = session["id"]

    try:
        # ---- delete messages
        supabase.table("messages") \
            .delete() \
            .or_(
                f"sender.eq.{username},receiver.eq.{username}"
            ) \
            .execute()

        # ---- delete reveal logs
        supabase.table("message_reveals") \
            .delete() \
            .eq("username", username) \
            .execute()

        # ---- delete profile
        supabase.table("user_profiles") \
            .delete() \
            .eq("id", user_id) \
            .execute()

        # ---- delete user row
        supabase.table("users") \
            .delete() \
            .eq("username", username) \
            .execute()

        # ---- logout
        session.clear()
        flash("Your account has been permanently deleted.", "info")
        return redirect("/signup")

    except Exception as e:
        flash(f"Error deleting account: {str(e)}", "error")
        return redirect("/profile")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        
        # Check if user exists with this email
        user_res = supabase.table("users").select("id").eq("email", email).execute()
        if not user_res.data:
            # Security: Don't reveal if email exists or not, but for this app maybe we should?
            # User requirement: "if users enter any invalid email which doesnt exist the page shouldnt crash"
            # I'll show a generic message or just pretend to send. 
            # But to be helpful I will show error for now as requested implicitly by "page shouldnt crash"
            # actually user said "verify its unique email and no other account exists... in signup"
            # For forgot pass: "if users enter any invalid email... page shouldnt crash"
            flash("If an account exists with this email, an OTP has been sent.", "info")
            # We can return here effectively hiding the user existence
            # BUT for the actual flow to work we need to generate OTP only if user exists
            # functionality wise: I need to verify user to reset password.
            return render_template("forgot_password.html")

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        
        # Determine expiration (optional, for now just store in session)
        session["reset_email"] = email
        session["reset_otp"] = otp
        
        # Send Email
        if send_otp_email(email, otp):
            return redirect("/verify-otp")
        else:
            flash("Failed to send email. Please try again.", "error")
            return render_template("forgot_password.html")

    return render_template("forgot_password.html")

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "reset_email" not in session or "reset_otp" not in session:
        return redirect("/forgot-password")

    if request.method == "POST":
        entered_otp = request.form.get("otp")
        if entered_otp == session["reset_otp"]:
            session["reset_verified"] = True
            return redirect("/reset-password")
        else:
            flash("Invalid OTP. Please try again.", "error")
            return render_template("verify_otp.html")

    return render_template("verify_otp.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if "reset_email" not in session or not session.get("reset_verified"):
        return redirect("/forgot-password")

    if request.method == "POST":
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")

        if password != cpassword:
            flash("Passwords do not match.", "error")
            return render_template("reset_password.html")
        
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("reset_password.html")

        email = session["reset_email"]
        
        # Update user password
        # Need to fetch username to log them in automatically? 
        # Requirement: "user gets logged in and then user gets another mail that their account password got updated"
        
        supabase.table("users").update({"password": password}).eq("email", email).execute()
        
        # Get username for session login
        user_data = supabase.table("users").select("username").eq("email", email).execute()
        if user_data.data:
            session["user"] = user_data.data[0]["username"]
        
        # Send confirmation email (Optional but good practice / requested?)
        # "user gets another mail that their account password got updated"
        # I'll skip the confirmation email implementation for now to save tokens/complexity unless strictly needed
        # actually prompt says: "user gets another mail that their account password got updated"
        # OK, I will send it.
        
        # Send confirmation email
        try:
            send_password_success_email(email)
        except Exception as e:
            print(f"Failed to send success email: {e}")
            pass
            pass
            
        # Clean up session
        session.pop("reset_otp", None)
        session.pop("reset_email", None)
        session.pop("reset_verified", None)
        
        return redirect("/dashboard")

    return render_template("reset_password.html")


if __name__ == "__main__":
    app.run()