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

def cover_page():
    
    col1, col2, col3 = st.columns([4,4,4])

    with col2:
        st.image("undip.png", use_column_width=True)
        
    # Tambahkan judul dengan rata tengah menggunakan HTML dan CSS
    st.markdown("<h1 style='text-align: center; font-size: 30px;'>APLIKASI PRAKIRAAN HARGA SAHAM BERBASIS WEB MENGGUNAKAN METODE TRIPLE EXPONENTIAL SMOOTHING<br>(STUDI KASUS: PT BANK RAKYAT INDONESIA TBK)</h1>", unsafe_allow_html=True)

    st.markdown("<p style='text-align: center; font-size: 20px;'><br>Bariq Unggul Pribadi<br>2120118120005</p>", unsafe_allow_html=True)

    st.markdown("<p style='text-align: center; font-size: 22px;'><br>Universitas Diponegoro<br>2023</p>", unsafe_allow_html=True)

    style = "<style>.row-widget.stButton {text-align: center;}</style>"
    st.markdown(style, unsafe_allow_html=True)

    if st.button("Login Page"):
        st.experimental_set_query_params(page="login")
    

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
            st.rerun()
        else:
            st.error("Login gagal. Mohon cek username dan password Anda.")

    # Tampilkan link signup
    signup_link.markdown("[Signup](?page=signup)")


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
                st.markdown("[Kembali ke Halaman Login](?page=login)")

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
    df['close'].ffill(inplace=True)

    st.title('Prakiraan Saham BBRI')

    # Dropdown untuk tanggal awal prakiraan
    start_date = pd.Timestamp('2023-10-19')



    # Dropdown untuk tanggal awal
    chosen_date = st.date_input("Pilih Tanggal Mulai Prakiraan", min_value=start_date, max_value=pd.Timestamp('2024-10-19'))
    
    chosen_date = pd.Timestamp(chosen_date)
    
    if chosen_date:
        # Dropdown untuk tanggal akhir prakiraan
        end_date = st.date_input("Pilih Batas Akhir Tanggal Prakiraan", max_value=pd.Timestamp('2024-10-19'))
        end_date = pd.Timestamp(end_date)  # Konversi end_date ke pandas.Timestamp

        # Validasi agar end_date tidak lebih awal daripada chosen_date
        if end_date < chosen_date:
            st.error("Batas Akhir Tanggal Prakiraan tidak boleh lebih awal daripada Tanggal Mulai Prakiraan.")
        else:
            # Menghitung jumlah hari antara tanggal awal dan tanggal akhir
            day = (end_date - start_date).days
            pred = model.forecast(day)
            pred = pd.DataFrame(pred, columns=['Harga'], index=pd.date_range(start=start_date, periods=day, freq='B'))
            pred.index.name = "Tanggal"

            # Konversi chosen_date ke datetime64[ns]
            

            # Membagi data prediksi menjadi dua bagian: sebelum dan setelah chosen_date
            pred_before_chosen_date = pred.loc[pred.index <= chosen_date]
            pred_after_chosen_date = pred.loc[pred.index > chosen_date]

            if st.button("Hasil"):
                st.subheader("Hasil Prakiraan:")
                st.dataframe(pred[chosen_date:end_date])

                st.subheader("Grafik Prakiraan:")
                fig, ax = plt.subplots(figsize=(24, 12))
                df['close'].plot(color="blue", legend=True, label='Data Asli')
                pred_before_chosen_date['Harga'].plot(color="orange", legend=True, label='Prakiraan dari 19 Oktober 2023', linestyle='--')
                pred_after_chosen_date['Harga'].plot(color="green", legend=True, label='Prakiraan Setelah Tanggal yang Dipilih')
                ax.legend(fontsize=20)
                ax.tick_params(axis='both', labelsize=18)
                ax.set_xlabel("Tanggal", fontsize=20)
                ax.set_ylabel("Harga Penutupan", fontsize=20)

                st.pyplot(fig)

def main():
    manage_login_status()

    # Check for the initial page query parameter
    params = st.experimental_get_query_params()
    initial_page = params.get("page", ["cover"])[0]

    # Periksa status login sesi pengguna
    if st.session_state.logged_in:
        # Tambahkan tombol log out
        logout_button = st.button("Logout")
        if logout_button:
            st.session_state.logged_in = False
            # st.experimental_set_query_params(page="cover")
            st.rerun()
        home_page()
    elif initial_page == "signup":
        signup_page()
    elif initial_page == "login":
        login_page()
    else:
        # Display the cover_page as the default page
        cover_page()

if __name__ == '__main__':
    main()