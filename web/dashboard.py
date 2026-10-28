from pathlib import Path
import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

# Añadir directorio raíz al sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from data.db import (
    load_db, save_db, get_stock, get_shopping, get_user_prefs,
    get_expenses, get_offers, add_or_update_stock_item, add_expense, update_user_prefs
)
from web.ai_comparator import compare_supermarket_offers, answer_ai_chat_query

# Configuración de página Streamlit
st.set_page_config(
    page_title="Expensa House | Centro de Control Inteligente",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
        h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0; }
        .stApp { background: #f5f7f2; }
        [data-testid="stSidebar"] { background: #163b35; }
        [data-testid="stSidebar"] * { color: #f4f7ee; }
        .hero { background: linear-gradient(120deg, #163b35 0%, #235c4d 62%, #8ead45 150%); padding: 24px 30px; border-radius: 12px; color: white; margin-bottom: 20px; }
        .hero h1 { color: white; font-size: 2.1rem; margin: 0 0 6px; }
        .hero p { color: #dbe9d7; margin: 0; font-size: 0.98rem; }
        .metric { background: white; border-left: 4px solid #8ead45; padding: 16px 18px; border-radius: 8px; box-shadow: 0 2px 12px rgba(22,59,53,.07); }
        .metric-label { color: #687771; font-size: .82rem; text-transform: uppercase; letter-spacing: .06em; }
        .metric-value { color: #163b35; font-family: 'Space Grotesk'; font-size: 1.7rem; font-weight: 700; margin-top: 3px; }
        .section-title { color: #163b35; font-family: 'Space Grotesk'; font-size: 1.15rem; font-weight: 700; margin: 18px 0 8px; }
        .stDataFrame { border-radius: 8px; overflow: hidden; }
        .bot-card { background-color: #ffffff; border-radius: 10px; padding: 18px; border: 1px solid #e1e8db; margin-bottom: 15px; }
        .redirect-btn { background-color: #163b35; color: white; padding: 10px 18px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 10px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def metric(label: str, value: str) -> None:
    st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

inject_styles()

# Inicialización de estado de sesión
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "📦 Stock e Inventario"
if "chatbot_last_msg" not in st.session_state:
    st.session_state["chatbot_last_msg"] = None
if "voice_query" not in st.session_state:
    st.session_state["voice_query"] = ""

# Carga de datos unificada en tiempo real con App Android
db = load_db()
stock_list = get_stock()
df_stock = pd.DataFrame(stock_list)

if df_stock.empty:
    df_stock = pd.DataFrame(columns=["name", "brand", "category", "stockQuantity", "inUseCount", "price"])

aliases = {"name": "producto", "brand": "marca", "category": "categoria", "stockQuantity": "stock", "inUseCount": "en_uso"}
df_stock = df_stock.rename(columns=aliases)
for col, default_val in [("marca", "Genérica"), ("categoria", "Comestibles"), ("stock", 0), ("en_uso", 0), ("precio", 0.0)]:
    if col not in df_stock:
        df_stock[col] = default_val

df_stock["stock"] = pd.to_numeric(df_stock["stock"], errors="coerce").fillna(0).astype(int)
df_stock["en_uso"] = pd.to_numeric(df_stock["en_uso"], errors="coerce").fillna(0).astype(int)
df_stock["precio"] = pd.to_numeric(df_stock["precio"], errors="coerce").fillna(0.0)
df_stock["total"] = df_stock["stock"] + df_stock["en_uso"]
df_stock["estado"] = df_stock["stock"].apply(lambda v: "Crítico" if v <= 1 else "Disponible")

# --- BARRA LATERAL (FILTRO IA Y RECONOCIMIENTO DE VOZ) ---
with st.sidebar:
    st.markdown("## 🏠 Expensa House")
    st.caption("Centro de control con sincronización en espejo Android/Web")
    st.markdown("🟢 **Sincronizado con App Móvil**")
    st.divider()

    st.markdown("### 🎙️ Búsqueda de Productos por Voz / IA")

    # Componente Web Speech API para Búsqueda por Voz en Navegador
    st.components.v1.html(
        """
        <div style="font-family: sans-serif; text-align: center;">
            <button id="micBtn" style="background-color: #8ead45; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%;">
                🎙️ Dictar por Voz
            </button>
            <p id="speechStatus" style="font-size: 11px; color: #dbe9d7; margin-top: 6px;">Haz clic para hablar</p>
        </div>
        <script>
            const micBtn = document.getElementById('micBtn');
            const status = document.getElementById('speechStatus');
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.lang = 'es-AR';
                recognition.continuous = false;

                micBtn.onclick = () => {
                    recognition.start();
                    status.innerText = "Escuchando... Hablá ahora";
                    micBtn.style.backgroundColor = "#e05252";
                };

                recognition.onresult = (event) => {
                    const text = event.results[0][0].transcript;
                    status.innerText = 'Dictado: "' + text + '"';
                    micBtn.style.backgroundColor = "#8ead45";

                    // Copiar al portapapeles y notificar
                    navigator.clipboard.writeText(text);
                    alert('Texto dictado: "' + text + '". Pégalo en la búsqueda.');
                };

                recognition.onerror = () => {
                    status.innerText = "Error o micrófono cancelado";
                    micBtn.style.backgroundColor = "#8ead45";
                };
            } else {
                status.innerText = "Dictado por voz disponible en Chrome/Edge";
            }
        </script>
        """,
        height=75
    )

    search_query = st.text_input("🔍 Filtro / Búsqueda IA", value=st.session_state["voice_query"], placeholder="Ej: leche, limpieza, critico...")
    selected_categories = st.multiselect("Filtrar Categoría", sorted(df_stock["categoria"].unique()) if not df_stock.empty else [])
    only_critical = st.toggle("Solo stock crítico (≤ 1)", value=False)

    st.divider()
    st.markdown("### 🔄 Sincronización Manual")
    if st.button("Forzar Recarga desde App"):
        st.cache_data.clear()
        st.rerun()

# Filtrar dataset de stock
filtered_df = df_stock.copy()
if search_query:
    filtered_df = filtered_df[
        filtered_df["producto"].str.contains(search_query, case=False, na=False) |
        filtered_df["marca"].str.contains(search_query, case=False, na=False) |
        filtered_df["categoria"].str.contains(search_query, case=False, na=False)
    ]
if selected_categories:
    filtered_df = filtered_df[filtered_df["categoria"].isin(selected_categories)]
if only_critical:
    filtered_df = filtered_df[filtered_df["stock"] <= 1]

# --- ENCABEZADO Y HERO ---
st.markdown(
    '<div class="hero">'
    '<h1>Tu Casa en Perspectiva (Web & Android Sync)</h1>'
    '<p>Panel espejo unificado: Inventario, Comparador de Ofertas con IA y Control Financiero.</p>'
    '</div>',
    unsafe_allow_html=True
)

# --- 🤖 CHATBOT INTERACTIVO BOTI HOUSE (3 OPCIONES CON REDIRECCIÓN DIRECTA A MÓDULO) ---
st.markdown('<div class="section-title">🤖 Boti House - Asistente Virtual IA</div>', unsafe_allow_html=True)
st.caption("Escribe tu número de opción (1, 2 o 3) o haz clic en los botones para recibir la respuesta e ir directamente al módulo correspondiente:")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("1️⃣ Encontrar Ofertas de Súper", use_container_width=True):
        st.session_state["bot_choice"] = "1"
with col2:
    if st.button("2️⃣ Presupuesto y Gastos", use_container_width=True):
        st.session_state["bot_choice"] = "2"
with col3:
    if st.button("3️⃣ Stock y Productos Faltantes", use_container_width=True):
        st.session_state["bot_choice"] = "3"

user_option = st.text_input("Ingresa el número de opción (1, 2 o 3) o escribe tu pregunta:", placeholder="Ejemplo: 1 o ¿qué falta comprar?")

if user_option.strip() in ["1", "2", "3"]:
    st.session_state["bot_choice"] = user_option.strip()

if "bot_choice" in st.session_state:
    choice = st.session_state["bot_choice"]
    st.markdown('<div class="bot-card">', unsafe_allow_html=True)

    if choice == "1":
        st.markdown("### 1️⃣ OPCIÓN ELEGIDA: Encontrar Ofertas en Supermercados")
        st.write("🔎 **Análisis IA de Promociones:**")
        criticos = df_stock[df_stock["stock"] <= 1]
        prod_target = criticos.iloc[0]["producto"] if not criticos.empty else "leche"
        res = compare_supermarket_offers(prod_target)

        st.info(f"Comparación activa para **{prod_target}**:")
        st.markdown(res["ai_analysis"]["verdict"])

        if st.button("🚀 IR AL MÓDULO DE OFERTAS", key="go_to_offers"):
            st.session_state["active_tab"] = "🏷️ Ofertas e IA de Súper"
            st.rerun()

    elif choice == "2":
        st.markdown("### 2️⃣ OPCIÓN ELEGIDA: Presupuesto Disponible y Gastos")
        prefs = get_user_prefs()
        budget = prefs.get("monthlyBudget", 0.0)
        spent = prefs.get("totalSpent", 0.0)
        remaining = budget - spent

        st.write(f"📊 **Estado Financiero:**")
        st.write(f"• Presupuesto Mensual: **${budget:,.2f}**")
        st.write(f"• Gastado Acumulado: **${spent:,.2f}**")
        st.write(f"• **Disponible Restante:** **${remaining:,.2f}**")

        if remaining < budget * 0.15:
            st.warning("⚠️ ¡Atención! Has consumido la mayor parte de tu presupuesto mensual.")
        else:
            st.success("✅ Tu presupuesto se encuentra saludable.")

        if st.button("🚀 IR AL MÓDULO DE PRESUPUESTO", key="go_to_budget"):
            st.session_state["active_tab"] = "💰 Presupuesto y Gastos"
            st.rerun()

    elif choice == "3":
        st.markdown("### 3️⃣ OPCIÓN ELEGIDA: Productos Faltantes y Stock")
        criticos = df_stock[df_stock["stock"] <= 1]
        st.write(f"📦 **Resumen de la Alacena:**")
        st.write(f"• Total Unidades en Casa: **{df_stock['total'].sum()}**")
        st.write(f"• Productos con Stock Crítico: **{len(criticos)}**")

        if not criticos.empty:
            st.warning("Productos que requieren reposición urgente:")
            st.dataframe(criticos[["producto", "marca", "categoria", "stock", "en_uso"]], hide_index=True)
        else:
            st.success("¡Tu alacena no tiene productos críticos en este momento!")

        if st.button("🚀 IR AL MÓDULO DE STOCK", key="go_to_stock"):
            st.session_state["active_tab"] = "📦 Stock e Inventario"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

elif user_option.strip():
    # Consulta abierta
    response = answer_ai_chat_query(user_option)
    st.info(f"🤖 **Boti House:**\n\n{response}")

st.divider()

# --- SELECCIÓN DE MÓDULOS DEL DASHBOARD ---
tabs = ["📦 Stock e Inventario", "🏷️ Ofertas e IA de Súper", "💰 Presupuesto y Gastos"]
selected_tab = st.radio(
    "Navegar Módulo:",
    tabs,
    index=tabs.index(st.session_state["active_tab"]) if st.session_state["active_tab"] in tabs else 0,
    horizontal=True
)
st.session_state["active_tab"] = selected_tab

# ==========================================
# MÓDULO 1: STOCK E INVENTARIO
# ==========================================
if selected_tab == "📦 Stock e Inventario":
    st.header("📦 Módulo de Alacena y Stock")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric("Unidades en Casa", f"{filtered_df['total'].sum()}")
    with m2:
        metric("Stock Crítico", f"{(filtered_df['stock'] <= 1).sum()}")
    with m3:
        metric("Valor Estimado", f"${(filtered_df['total'] * filtered_df['precio']).sum():,.0f}")
    with m4:
        metric("Categorías Activas", f"{filtered_df['categoria'].nunique()}")

    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown('<div class="section-title">Distribución por Categoría</div>', unsafe_allow_html=True)
        cat_data = filtered_df.groupby("categoria", as_index=False)["total"].sum().sort_values("total", ascending=False)
        fig_bar = px.bar(cat_data, x="total", y="categoria", orientation="h", color="total", color_continuous_scale=["#8ead45", "#163b35"])
        fig_bar.update_layout(height=280, margin=dict(l=0, r=10, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        st.markdown('<div class="section-title">Estado del Inventario</div>', unsafe_allow_html=True)
        status_data = filtered_df["estado"].value_counts().reset_index()
        status_data.columns = ["estado", "cantidad"]
        fig_pie = px.pie(status_data, values="cantidad", names="estado", hole=0.6, color="estado", color_discrete_map={"Crítico": "#e05252", "Disponible": "#8ead45"})
        fig_pie.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown('<div class="section-title">Inventario Completo (Sincronizado en Espejo)</div>', unsafe_allow_html=True)
    st.dataframe(
        filtered_df[["producto", "marca", "categoria", "stock", "en_uso", "total", "precio", "estado"]].rename(
            columns={"producto": "Producto", "marca": "Marca", "categoria": "Categoría", "stock": "Cerradas", "en_uso": "En Uso", "total": "Total", "precio": "Precio", "estado": "Estado"}
        ),
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# MÓDULO 2: COMPARADOR DE OFERTAS
# ==========================================
elif selected_tab == "🏷️ Ofertas e IA de Súper":
    st.header("🏷️ Módulo Comparador de Ofertas de Supermercados")
    st.caption("Compara precios entre Coto, Carrefour, Día, Jumbo y ChangoMás cruzados con el stock de tu casa.")

    prod_query = st.text_input("🔍 Producto a comparar:", value="leche", placeholder="Ej: cafe, dulce de leche, detergente")
    if prod_query:
        comparison = compare_supermarket_offers(prod_query)
        st.markdown(comparison["ai_analysis"]["verdict"])

        st.subheader("Detalle de Ofertas Detectadas:")
        df_offers = pd.DataFrame(comparison["offers"])
        if not df_offers.empty:
            st.dataframe(
                df_offers[["store", "brand", "regular_price", "promo_price", "unit_effective_price", "promo_text", "saving_percent"]].rename(
                    columns={
                        "store": "Supermercado",
                        "brand": "Marca",
                        "regular_price": "Precio Lista ($)",
                        "promo_price": "Precio Promo ($)",
                        "unit_effective_price": "Costo Ef. Unic. ($)",
                        "promo_text": "Promoción",
                        "saving_percent": "% Ahorro"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

# ==========================================
# MÓDULO 3: PRESUPUESTO Y GASTOS
# ==========================================
elif selected_tab == "💰 Presupuesto y Gastos":
    st.header("💰 Módulo de Presupuesto Mensual y Gastos")

    prefs = get_user_prefs()
    expenses_list = get_expenses()

    b1, b2, b3 = st.columns(3)
    with b1:
        metric("Presupuesto Mensual", f"${prefs.get('monthlyBudget', 0.0):,.2f}")
    with b2:
        metric("Total Gastado", f"${prefs.get('totalSpent', 0.0):,.2f}")
    with b3:
        rem = prefs.get('monthlyBudget', 0.0) - prefs.get('totalSpent', 0.0)
        metric("Disponible", f"${rem:,.2f}")

    st.progress(min(1.0, prefs.get('totalSpent', 0.0) / max(1.0, prefs.get('monthlyBudget', 1.0))))

    st.markdown('<div class="section-title">Historial de Tickets y Gastos Cargados</div>', unsafe_allow_html=True)
    if expenses_list:
        df_exp = pd.DataFrame(expenses_list)
        st.dataframe(
            df_exp[["category", "amount", "note"]].rename(
                columns={"category": "Categoría", "amount": "Monto ($)", "note": "Detalle / Nota"}
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay gastos registrados aún.")
