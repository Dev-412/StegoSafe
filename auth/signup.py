from database.client import supabase
def signup_user(username, password, cpassword):

    # Insert into Supabase
    supabase.table("users").insert({
        "username": username,
        "password": password,  #hash password
        "public_key":0,
        "private_key":0
    }).execute()

    return "success"
