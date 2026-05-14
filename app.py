import streamlit as st

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Asistente Renal", layout="centered")

# --- ESTILO (para centrar el login) ---
st.markdown("""
    <style>
    .login-box {
        max-width: 350px;
        margin: auto;
        padding: 30px;
        border-radius: 10px;
        background-color: #f5f5f5;
        box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- ESTADO DE LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- TÍTULO PRINCIPAL ---
st.markdown("<h1 style='text-align: center;'>🩺 Asistente Renal</h1>", unsafe_allow_html=True)

# --- LOGIN FICTICIO ---
if not st.session_state.logged_in:
    with st.container():
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)

        st.subheader("Iniciar sesión")

        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")

        if st.button("Entrar"):
            # 👉 LOGIN FICTICIO (puedes cambiar esto)
            if username == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.success("Acceso concedido")
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

        st.markdown("</div>", unsafe_allow_html=True)

# --- CONTENIDO PRIVADO ---
else:
    st.success("Bienvenido 👋")

    st.write("Aquí empieza tu app privada")

    if st.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.rerun()
