import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import hashlib
import base64
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'U8GOJNKCH3NC1MP7')
# Initialize database
def init_db():
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_pic BLOB
        )
    """)
    conn.commit()
    conn.close()
    # Hashing function for secure passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
# Add new user to the database
def add_user(username, email, password):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                   (username, email, hash_password(password)))
    conn.commit()
    conn.close()
    # Authenticate user
def authenticate_user(username, password):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                   (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user
# Fetch user data
def fetch_user_data(username):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user
# Update profile picture
def update_profile_pic(username, profile_pic):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET profile_pic = ? WHERE username = ?", 
                   (profile_pic, username))
    conn.commit()
    conn.close()
# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'user_data' not in st.session_state:
    st.session_state['user_data'] = {}

# Apply custom CSS for styling
def apply_custom_css():
    st.markdown(
        """
        <style>
        body {
            background-color: #1e1e2f;
            color: #ffffff;
        }
        .profile-pic {
            display: block;
            margin: 0 auto;
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
        }
        .stButton > button {
            background: linear-gradient(90deg, #27AE60, #1E90FF);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
        }
        .stButton > button:hover {
            background: linear-gradient(90deg, #1E90FF, #27AE60);
            transform: scale(1.05);
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th {
            background-color: #4CAF50;
            color: white;
            padding: 8px;
            text-align: center;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Hashing function for secure passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Registration function
def register():
    st.title("Register")
    username = st.text_input("Username", key="register_username")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")

    if st.button("Register", key="register_button"):
        if not username or not email or not password:
            st.warning("Please fill in all fields.")
        elif username in st.session_state['user_data']:
            st.warning("Username already exists!")
        elif password != confirm_password:
            st.warning("Passwords do not match!")
        else:
            st.session_state['user_data'][username] = {
                "email": email,
                "password": hash_password(password),
                "profile_pic": None,
            }
            st.success("Registration successful! You can now log in.")

# Login function
def login():
    st.title("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_button"):
        hashed_password = hash_password(password)
        if username in st.session_state['user_data'] and st.session_state['user_data'][username]["password"] == hashed_password:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success(f"Welcome, {username}")
        else:
            st.error("Invalid username or password")

# Logout function
def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.info("You have logged out.")

# Profile Section
def profile_section():
    username = st.session_state['username']
    user_data = st.session_state['user_data'][username]

    st.title("My Profile")
    if user_data['profile_pic']:
        st.image(user_data['profile_pic'], width=150)
    else:
        st.info("No profile picture uploaded yet.")

    uploaded_file = st.file_uploader("Upload Profile Picture", type=["jpg", "jpeg", "png"], key="upload_profile_pic")
    if uploaded_file:
        user_data['profile_pic'] = uploaded_file.read()
        st.session_state['user_data'][username] = user_data
        st.success("Profile picture updated!")

    st.subheader("User Details")
    st.write(f"*Username:* {username}")
    st.write(f"*Email:* {user_data['email']}")

# Display Profile Picture at Top
def display_top_profile():
    username = st.session_state['username']
    user_data = st.session_state['user_data'][username]

    if user_data['profile_pic']:
        profile_pic_base64 = base64.b64encode(user_data['profile_pic']).decode('utf-8')
        profile_pic_html = f'<img class="profile-pic" src="data:image/png;base64,{profile_pic_base64}" alt="Profile Picture">'
    else:
        profile_pic_html = '<img class="profile-pic" src="https://via.placeholder.com/80" alt="Default Profile Picture">'

    st.markdown(profile_pic_html, unsafe_allow_html=True)

# Forecast Stock Prices
def forecast_prices(df):
    df['Days'] = (df['Date'] - df['Date'].min()).dt.days
    X = df[['Days']]
    y = df['Price']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    st.write(f"#### Model Mean Squared Error (MSE): {mse:.2f}")

    forecast_days = 30
    future_dates = pd.date_range(start=df['Date'].max() + datetime.timedelta(days=1), periods=forecast_days)
    future_days = (future_dates - df['Date'].min()).days
    future_prices = model.predict(future_days.values.reshape(-1, 1))

    forecast_df = pd.DataFrame({
        "Date": future_dates,
        "Predicted Price": future_prices
    })
    st.write("### 🔮 Forecasted Prices for the Next 30 Days")
    st.dataframe(forecast_df.style.format({"Predicted Price": "${:,.2f}"}))
    
    fig_forecast = px.line(
        forecast_df, x="Date", y="Predicted Price", title="Forecasted Price Trend",
        color_discrete_sequence=["#27AE60"], markers=True
    )
    st.plotly_chart(fig_forecast)

# Market Trends Analysis
def market_trends_analysis():
    st.title("Market Trends Analysis")
    date_range = st.date_input("Select Date Range", [])
    market_symbol = st.text_input("Enter Market Symbol", "SPX")

    if st.button("Fetch Market Data"):
        if len(date_range) == 2:
            start_date, end_date = date_range

            dates = pd.date_range(start=start_date, end=end_date)
            data = {
                "Date": dates,
                "Price": np.random.randint(1000, 5000, len(dates)),
                "Volume": np.random.randint(10000, 100000, len(dates))
            }
            df = pd.DataFrame(data)

            st.write(f"### Data for {market_symbol} ({start_date} to {end_date})")
            st.dataframe(df.style.highlight_max(subset="Price", axis=0))

            st.markdown("### 📈 Price and Volume Trends")
            fig_price = px.line(df, x="Date", y="Price", title="Price Trend Over Time")
            st.plotly_chart(fig_price)

            fig_vol = px.bar(df, x="Date", y="Volume", title="Volume Trend Over Time", color="Volume", color_continuous_scale="Viridis")
            st.plotly_chart(fig_vol)

            forecast_prices(df)
        else:
            st.error("Please select a valid date range.")

# Main Function
def main():
    apply_custom_css()
    if not st.session_state['logged_in']:
        st.sidebar.title("Please Login or Register")
        option = st.sidebar.radio("Choose an Option", ("Login", "Register"))
        if option == "Register":
            register()
        elif option == "Login":
            login()
    else:
        display_top_profile()
        st.sidebar.title("Welcome!")
        menu_option = st.sidebar.radio("Menu", ["Market Trends", "My Profile"])
        if st.sidebar.button("Logout"):
            logout()
        elif menu_option == "Market Trends":
            market_trends_analysis()
        elif menu_option == "My Profile":
            profile_section()

if __name__ == "__main__":
    main()
