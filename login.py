import os
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

# This should be on top of your script
cookies = EncryptedCookieManager(
    prefix="ktosiek/streamlit-cookies-manager/",
    password=os.environ.get("COOKIES_PASSWORD", "My secret password"),
)

# User roles (you could extend this with more users and their roles)
users_db = {
    'manager': {'password': 'qwe', 'role': 'manager'},
    'guest': {'password': 'asd', 'role': 'guest'},
    'sajjad': {'password': '123', 'role': 'trader'},
    'akbar': {'password': '456', 'role': 'trader'},
}

# Check if the cookies are ready
if not cookies.ready():
    st.stop()

# Helper function to login the user and check their credentials
def login_user(username, password):
    user = users_db.get(username)
    if user and user['password'] == password:
        return user['role']
    return None

# Check if the user is logged in by looking for a cookie
logged_in = cookies.get("logged_in", "False") == "True"  # Convert cookie string back to boolean

# If the user is not logged in, show the login form
if not logged_in:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        role = login_user(username, password)
        if role:
            # Set a cookie indicating the user is logged in and store the user role
            cookies["logged_in"] = "True"
            cookies["username"] = username
            cookies["role"] = role
            cookies.save()  # Save the cookies and trigger a rerun
            st.success("Logged in successfully!")
            st.rerun()  # Rerun the app after login
        else:
            st.error("Invalid credentials")
else:
    # If the user is logged in, retrieve the role from the cookies
    username = cookies.get('username')
    role = cookies.get('role')

    # Show content based on the role
    st.title(f"Welcome, {username}")
    
    if role == 'manager':
        st.write("You have full access to the app.")
    
    
    # Optionally, allow the user to log out
    if st.button("Logout"):
        cookies["logged_in"] = ""  # Effectively delete the cookie by setting an empty string
        cookies["username"] = ""  # Effectively delete the username cookie
        cookies["role"] = ""  # Effectively delete the role cookie
        cookies.save()  # Save the cookies and trigger a rerun
        st.rerun()  # Rerun the app after logout
