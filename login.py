import streamlit as st
import sqlite3
import pickle
import pandas as pd
import matplotlib.pyplot as plt

# Membuat koneksi dengan database SQLite
conn = sqlite3.connect('BBRI.db')
c = conn.cursor()

# Membuat tabel user jika belum ada
c.execute('''CREATE TABLE IF NOT EXISTS users
             (ID INTEGER PRIMARY KEY, username TEXT, password TEXT)''')

# Fungsi untuk mengelola status login pengguna
def manage_login_status():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

def login_page():
    # Tampilan halaman login
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")
    signup_link = st.empty()

    if login_button:
        # Melakukan proses login dan validasi
        if validate_login(username, password):
            # Set status login
            st.session_state.logged_in = True
            # Reset halaman
            st.experimental_rerun()
        else:
            st.error("Login gagal. Mohon cek username dan password Anda.")

    # Tampilkan link signup
    signup_link.markdown("[Signup](?signup=True)")

def signup_page():
    # Tampilan halaman signup
    st.title("Sign Up")
    new_username = st.text_input("Username baru")
    new_password = st.text_input("Password baru", type="password")
    signup_button = st.button("Signup")

    if signup_button:
        # Melakukan proses pendaftaran dan validasi
        if new_username.strip() == "" or new_password.strip() == "":
            st.warning("Mohon isi username dan password dengan benar.")
        else:
            if username_exists(new_username):
                st.warning("Username sudah digunakan. Mohon pilih username lain.")
            else:
                # Menyimpan username dan password ke database
                insert_user(new_username, new_password)
                st.success("Akun berhasil dibuat. Silakan login.")
                # Tampilkan tombol kembali ke halaman login
                st.markdown("[Kembali ke Halaman Login](?signup=False)")

def validate_login(username, password):
    # Melakukan validasi login
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    return result is not None

def username_exists(username):
    # Mengecek apakah username sudah ada dalam database
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    result = c.fetchone()
    return result is not None

def insert_user(username, password):
    # Menyimpan username dan password ke database
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

def home_page():
    # Tampilan halaman utama setelah login
    model = pickle.load(open('prakiraan_sahamBBRI.sav', 'rb'))

    df = pd.read_excel('BBRI.xlsx')
    df['date'] = pd.to_datetime(df['date'])
    df.set_index(['date'], inplace=True)
    df = df.asfreq('B')
    df.index.freq = 'B'
    df['close'].fillna(method='ffill', inplace=True)

    st.title('Prakiraan Saham BBRI')
    day = st.slider("Tentukan Hari", 1, 300, step=1)

    pred = model.forecast(day)
    pred = pd.DataFrame(pred, columns=['close'])

    if st.button("Hasil"):
        st.subheader("Hasil Prakiraan:")
        st.dataframe(pred)

        st.subheader("Grafik Prakiraan:")
        fig, ax = plt.subplots(figsize=(24, 12))  # Set the figure size
        df['close'].plot(color="blue", legend=True, label='Data Asli')
        pred['close'].plot(color="orange", legend=True, label='Prakiraan')
        st.pyplot(fig)

def main():
    manage_login_status()
    # Periksa status login sesi pengguna
    if st.session_state.logged_in:
        # Tambahkan tombol log out
        logout_button = st.button("Log Out")
        if logout_button:
            st.session_state.logged_in = False
        home_page()
    else:
        signup = st.experimental_get_query_params().get("signup")
        if signup and signup[0] == "True":
            signup_page()
        else:
            login_page()

if __name__ == '__main__':
    main()
