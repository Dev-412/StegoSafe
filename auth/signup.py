from database.client import supabase
def signup_user(username, password, cpassword):

    # Insert into Supabase
    supabase.table("users").insert({
        "username": username,
        "password": password,  #hash password
        "public_key":0,
        "private_key":0
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
        "show_online_status": True
    }).execute()

    return "success"
