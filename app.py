import streamlit as st
from pymongo import MongoClient
import bcrypt
from datetime import datetime
import base64

# MongoDB Connection
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client["e_commerce"]
products_collection = db["products"]
carts_collection = db["carts"]
users_collection = db["users"]
orders_collection = db["orders"]

# Password hashing
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# Function to encode local image
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Set background and center title
def set_background(image_file="bg.jpg"):
    bin_str = get_base64(image_file)
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{bin_str}");
                background-size: cover;
                background-position: center;
                color: white;
            }}
            .title-center {{
                text-align: center;
                font-size: 50px;
                font-weight: bold;
            }}
            .remove-btn {{
                background-color: #ff4b4b; 
                color: white; 
                padding: 5px 15px; 
                border-radius: 8px; 
                border: none; 
                cursor: pointer; 
                float: right; 
                margin-left: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #222222;
                color: blue;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ==============================
# Your login_page, home_page, admin_panel, cart_page, orders_page
# (No changes needed in those functions, keep your original code)
# ==============================

# Main Function
def main():
    # Use your local image here, e.g. bg.jpg in project folder
    set_background("bg.jpg")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None

    if not st.session_state.logged_in:
        login_page()
        return

    menu = ["Home", "Cart", "Orders", "Admin Panel", "Logout"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    elif choice == "Home":
        home_page()

    elif choice == "Cart":
        cart_page()

    elif choice == "Orders":
        orders_page()

    elif choice == "Admin Panel":
        admin_panel()

if __name__ == "__main__":
    main()
