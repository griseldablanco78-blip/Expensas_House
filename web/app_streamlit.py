import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from data.db import load_db, get_stock, get_user_prefs, get_expenses
from web.ai_comparator import compare_supermarket_offers, answer_ai_chat_query

st.set_page_config(page_title="Expensa House - Dashboard IA", page_icon="🏠", layout="wide")

st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    h1, h2, h3 { color: #ff4b4b; }
    .metric-card {
        background: linear-gradient(135deg, #262730, #3a3f47);
        color: #e0e0e0;
        padding: 18px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    .metric-card h2 { color: #ffef5b; font-weight: bold; }
    .metric-card h3 { color: #ffffff; }
    .bot-box {
    background-color: #1f232a;
    padding: 16px;
    border-radius: 10px;
    border: 1px solid #363b44;
    margin-top: 10px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.bot-box:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.6);
}
/* Streamlit button animations */
.stButton>button {
    transition: background-color 0.3s ease, transform 0.2s ease;
    background-color: #ff4b4b;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 0.5rem 1rem;
}
.stButton>button:hover {
    background-color: #ff6b6b;
    transform: scale(1.05);
}
    </style>
    """,
    unsafe_allow_html=True)

st.title("🏠 Expensa House - Centro de Control e Inteligencia Artificial")
st.caption("Sincronización en Espejo Android / Web & Asistente Boti House")

# Carga de base de datos en tiempo real
db = load_db()
stock_data = get_stock()
df_stock = pd.DataFrame(stock_data)

if not df_stock.empty:
    for col, val in [("brand", "Genérica"), ("category", "Comestibles"), ("stockQuantity", 0), ("inUseCount", 0), ("price", 0.0)]:
        if col not in df_stock:
            df_stock[col] = val
    df_stock["total"] = df_stock["stockQuantity"] + df_stock["inUseCount"]
else:
    df_stock = pd.DataFrame(columns=["name", "brand", "category", "stockQuantity", "inUseCount", "price", "total"])

# --- METRICAS DE CABECERA ---
st.header("📊 Métricas Consolidadas")
k1, k2, k3, k4 = st.columns(4)

total_units = df_stock["total"].sum() if not df_stock.empty else 0
crit_count = (df_stock["stockQuantity"] <= 1).sum() if not df_stock.empty else 0
user_prefs = get_user_prefs()
budget = user_prefs.get("monthlyBudget", 0.0)
spent = user_prefs.get("totalSpent", 0.0)

with k1:
    st.markdown(f"<div class='metric-card'><h3>Unidades en Casa</h3><h2>{total_units}</h2></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='metric-card'><h3>Stock Crítico</h3><h2>{crit_count}</h2></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='metric-card'><h3>Presupuesto Restante</h3><h2>${(budget - spent):,.2f}</h2></div>", unsafe_allow_html=True)
with k4:
    st.markdown("<div class='metric-card'><h3>Sincronización App</h3><h2>🟢 Activa</h2></div>", unsafe_allow_html=True)

st.divider()

# --- CHATBOT BOTI HOUSE CON 3 OPCIONES Y REDIRECCIÓN DIRECTA A MÓDULOS ---
st.sidebar.title("🔎 Búsqueda de Ofertas")
product_query = st.sidebar.text_input("Producto a buscar", placeholder="ej. leche Serena 1L")
st.header("🤖 Boti House - Chatbot IA (3 Opciones con Redirección Directa)")
st.markdown("Elige una opción por número o haz clic para ver la respuesta e ir directamente al módulo correspondiente:")

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("1️⃣ Encontrar Ofertas Súper"):
        st.session_state["bot_select"] = "1"
with c2:
    if st.button("2️⃣ Presupuesto Disponible"):
        st.session_state["bot_select"] = "2"
with c3:
    if st.button("3️⃣ Ver Productos Faltantes"):
        st.session_state["bot_select"] = "3"

user_in = st.text_input("Ingresa el número (1, 2 o 3) o consulta personalizada:")
if user_in.strip() in ["1", "2", "3"]:
    st.session_state["bot_select"] = user_in.strip()

if "bot_select" in st.session_state:
    sel = st.session_state["bot_select"]
    st.markdown('<div class="bot-box">', unsafe_allow_html=True)
    
    if sel == "1":
        st.subheader("1️⃣ Respuesta IA: Comparador de Ofertas de Supermercados")
        query = product_query if product_query else "leche"
        res = compare_supermarket_offers(query)
        img_url = res.get("product_image", "https://via.placeholder.com/200")
        st.image(img_url, width=200, caption=query)
        st.dataframe(pd.DataFrame(res["offers"]), width='stretch', hide_index=True)
        st.markdown(res["ai_analysis"]["verdict"])
        st.info("💡 Módulo destino: **Ofertas e Inteligencia de Mercado**")
        
    elif sel == "2":
        st.subheader("2️⃣ Respuesta IA: Presupuesto Disponible y Gastos")
        st.write(f"• Presupuesto Asignado: **${budget:,.2f}**")
        st.write(f"• Gastado en Tickets: **${spent:,.2f}**")
        st.write(f"• **Saldo Disponible:** **${(budget - spent):,.2f}**")
        st.info("💡 Módulo destino: **Presupuesto y Finanzas Familiar**")
        
    elif sel == "3":
        st.subheader("3️⃣ Respuesta IA: Productos Faltantes en Alacena")
        crit = df_stock[df_stock["stockQuantity"] <= 1]
        st.write(f"Tiene **{len(crit)}** producto(s) que requieren reposición:")
        if not crit.empty:
            st.dataframe(crit[["name", "brand", "category", "stockQuantity", "inUseCount"]])
        st.info("💡 Módulo destino: **Inventario de Alacena**")
        
    st.markdown('</div>', unsafe_allow_html=True)

elif user_in.strip():
    resp = answer_ai_chat_query(user_in)
    st.info(f"🤖 **Boti House:** {resp}")

st.divider()

# --- MÓDULOS DE NAVEGACIÓN ---
tab1, tab2, tab3 = st.tabs(["📦 Inventario de Stock", "🏷️ Ofertas e IA", "💰 Presupuesto y Gastos"])

with tab1:
    st.subheader("📦 Alacena e Inventario Completo")
    if not df_stock.empty:
        st.dataframe(df_stock[["name", "brand", "category", "stockQuantity", "inUseCount", "total", "price"]], width='stretch', hide_index=True)
    else:
        st.info("No hay productos cargados en el inventario.")

with tab2:
    st.subheader("🏷️ Comparador de Ofertas con IA")
    q = st.text_input("Buscar mejores ofertas para:", value="aceite de girasol")
    if q:
        comp = compare_supermarket_offers(q)
        st.markdown(comp["ai_analysis"]["verdict"])
        st.dataframe(pd.DataFrame(comp["offers"]), width='stretch', hide_index=True)

with tab3:
    st.subheader("💰 Presupuesto Mensual y Gastos")
    st.write(f"• Presupuesto: **${budget:,.2f}** | Gastado: **${spent:,.2f}** | Restante: **${(budget - spent):,.2f}**")
    exps = get_expenses()
    if exps:
        st.dataframe(pd.DataFrame(exps), width='stretch', hide_index=True)
