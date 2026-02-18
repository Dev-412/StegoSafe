from database.client import supabase
from auth.RSA import *
def signup_user(username, password, email):

    # Check if email already exists
    existing_user = supabase.table("users").select("email").eq("email", email).execute()
    if existing_user.data:
        return "Email already registered"

    pub, priv = generate_keys()
    # Insert into Supabase
    supabase.table("users").insert({
        "username": username,
        "password": password,  #hash password
        "email": email,
        "public_key":pub,
        "private_key":priv
    }).execute()

    # fetch id
    user = supabase.table("users") \
        .select("id") \
        .eq("username", username) \
        .single() \
        .execute()

    user_id = user.data["id"]

    # create default profile
    supabase.table("user_profiles").insert({
        "id": user_id,
        "profile_pic": "https://qliexogopxzdabruzeqb.supabase.co/storage/v1/object/public/avatars/default/blank.png",
        "bio": "Hey there! I'm new 👋",
        "theme": "Default",
        "status": True
    }).execute()

    return "success"
