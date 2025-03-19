import streamlit as st
from pymongo import MongoClient
import bcrypt
from datetime import datetime
from io import BytesIO

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

# Set background and center title
def set_background():
    st.markdown(
        """
        <style>
            .stApp {
                background: url('https://www.pixelstalk.net/wp-content/uploads/image12/A-sleek-3D-black-spiral-gently-rotating-in-a-dark.jpg');  /* Use your local image file or URL here */
                background-size: cover;
                background-position: center;
                color: white;
            }
            .title-center {
                text-align: center;
                font-size: 50px;
                font-weight: bold;
            }
            .remove-btn {
                background-color: #ff4b4b; 
                color: white; 
                padding: 5px 15px; 
                border-radius: 8px; 
                border: none; 
                cursor: pointer; 
                float: right; 
                margin-left: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #222222;
                color: blue;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

# Login Page
def login_page():
    st.markdown("<h1 class='title-center'>WELCOME TO NOVACART</h1>", unsafe_allow_html=True)
    
    # Check if the user clicked on the 'Sign Up' button
    if "signup" not in st.session_state:
        st.session_state.signup = False

    # If user clicked on 'Sign Up', show the sign-up form
    if st.session_state.signup:
        # Display Sign Up Form
        st.subheader("Sign Up")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Sign Up"):
            if password != confirm_password:
                st.error("❌ Passwords do not match!")
            elif users_collection.find_one({"username": username}):
                st.error("❌ Username already exists!")
            else:
                hashed_password = hash_password(password)
                users_collection.insert_one({"username": username, "password": hashed_password})
                st.success("✅ Account created successfully! Please log in.")
                st.session_state.signup = False
                st.session_state.user = username
                st.session_state.logged_in = True
                st.rerun()

        # Back to Login Option
        if st.button("Back to Login"):
            st.session_state.signup = False
            st.rerun()

    else:
        # Display Login Form
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        # Create two columns for the buttons
        col1, col2 = st.columns([3, 1])  # First column 3 width, second column 1 width

        with col1:
            login_btn = st.button("Login")

        with col2:
            signup_btn = st.button("Sign Up")

        if signup_btn:
            st.session_state.signup = True
            st.rerun()

        if login_btn:
            user = users_collection.find_one({"username": username})
            if user and verify_password(password, user["password"]):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success("✅ Logged in successfully!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials!")

# Home Page (Showing Products)
def home_page():
    st.markdown("<h1 class='title-center'>NOVACART.com</h1>", unsafe_allow_html=True)

    categories = products_collection.distinct("category")
    selected_category = st.selectbox("Select Category", ["All"] + categories)

    query = {} if selected_category == "All" else {"category": selected_category}
    products = list(products_collection.find(query))

    if products:
        cols = st.columns(3)
        for idx, product in enumerate(products):
            with cols[idx % 3]:
                image_data = product.get("image")
                st.image(image_data if image_data else "https://via.placeholder.com/200", width=200)
                st.write(f"**{product['name']}**")
                st.write(f"{product['price']} INR")
                quantity = st.number_input(f"Qty ({product['name']})", min_value=1, max_value=product['stock'], key=product['name'])
                
                if st.button(f"Add to Cart - {product['name']}", key=f"add_{product['name']}"):
                    cart_item = carts_collection.find_one({"user": st.session_state.user, "name": product["name"]})
                    if cart_item:
                        carts_collection.update_one({"_id": cart_item["_id"]}, {"$inc": {"quantity": quantity}})
                    else:
                        carts_collection.insert_one({
                            "user": st.session_state.user,
                            "name": product["name"],
                            "price": product["price"],
                            "quantity": quantity
                        })
                    st.success(f"✅ {product['name']} added to cart!")
                    st.rerun()

# Admin Panel - (Manage Products :Add, Update, Remove)
def admin_panel():
    st.markdown("<h1 class='title-center'>Admin Panel - Manage Products</h1>", unsafe_allow_html=True)
    
    option = st.selectbox("Choose Action", ["Add Product", "Update Product", "Remove Product"])

    if option == "Add Product":
        with st.form("add_product_form"):
            name = st.text_input("Product Name")
            category = st.text_input("Category")
            price = st.number_input("Price (INR)", min_value=1, value=1)  # Ensure both min_value and value are integers
            stock = st.number_input("Stock Quantity", min_value=1, value=1)  # Same for stock
            image_file = st.file_uploader("Upload Product Image", type=["jpg", "jpeg", "png"])

            submit_button = st.form_submit_button(label="Add Product")  # Submit button

            if submit_button:
                if image_file:
                    image_data = image_file.read()
                else:
                    image_data = None
                products_collection.insert_one({
                    "name": name,
                    "category": category,
                    "price": price,
                    "stock": stock,
                    "image": image_data
                })
                st.success(f"✅ Product '{name}' added successfully!")

    elif option == "Update Product":
        product_names = [product['name'] for product in products_collection.find()]
        selected_product = st.selectbox("Select Product to Update", product_names)
        product = products_collection.find_one({"name": selected_product})

        with st.form("update_product_form"):
            # Ensure both min_value and value are integers
            name = st.text_input("Product Name", value=product.get('name', ''))
            category = st.text_input("Category", value=product.get('category', ''))
            price = st.number_input("Price (INR)", min_value=1, value=int(product.get('price', 1)))  # Ensure price is an integer
            stock = st.number_input("Stock Quantity", min_value=1, value=int(product.get('stock', 1)))  # Ensure stock is an integer
            image_file = st.file_uploader("Upload Product Image", type=["jpg", "jpeg", "png"])

            submit_button = st.form_submit_button(label="Update Product")  # Submit button
            
            if submit_button:
                if image_file:
                    image_data = image_file.read()
                else:
                    image_data = product.get("image")
                products_collection.update_one(
                    {"_id": product["_id"]},
                    {"$set": {"name": name, "category": category, "price": price, "stock": stock, "image": image_data}}
                )
                st.success(f"✅ Product '{name}' updated successfully!")

    elif option == "Remove Product":
        product_names = [product['name'] for product in products_collection.find()]
        selected_product = st.selectbox("Select Product to Remove", product_names)
        if st.button(f"Remove {selected_product}"):
            products_collection.delete_one({"name": selected_product})
            st.success(f"✅ Product '{selected_product}' removed successfully!")


# Cart Page (Updated)
def cart_page():
    st.subheader("🛒 Your Shopping Cart")
    cart_items = list(carts_collection.find({"user": st.session_state.user}))

    if cart_items:
        total_price = sum(item["price"] * item["quantity"] for item in cart_items)

        # Display Cart Items in Simple Format
        for item in cart_items:
            col1, col2, col3 = st.columns([3, 1, 1])  # Create three columns
            with col1:
                st.write(f"**{item['name']}**")
                st.write(f"Price: {item['price']} INR")
                st.write(f"Quantity: {item['quantity']}")
            with col3:
                if st.button(f"Remove ", key=f"remove_{item['_id']}"):
                    carts_collection.delete_one({"_id": item["_id"]})
                    st.success(f"✅ {item['name']} removed from cart!")
                    st.rerun()

        # Display Total Price
        st.markdown(f"### 🏷️ Total Price: **{total_price} INR**")

        if st.button("✅ Proceed to Checkout"):
            try:
                orders_collection.insert_one({
                    "user": st.session_state.user,
                    "items": cart_items,
                    "total": total_price,
                    "timestamp": datetime.now(),
                })

                carts_collection.delete_many({"user": st.session_state.user})
                st.success("✅ Order placed successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Order placement failed: {e}")
    else:
        st.info("🛒 Your cart is empty.")

# Orders Page
def orders_page():
    st.subheader("📦 Your Orders")
    user_orders = list(orders_collection.find({"user": st.session_state.user}))

    if user_orders:
        for order in user_orders:
            st.write(f"### 🛍️ Order Date: {order['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            for item in order["items"]:
                st.write(f"- **{item['name']}** - {item['price']} INR x {item['quantity']}")
            st.write(f"**💰 Total: {order['total']} INR**")
            st.markdown("---")
    else:
        st.info("📭 You have no orders yet.")

# Main Function
def main():
    set_background()

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
