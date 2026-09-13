from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Expensas House | Centro de control",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)


DEMO_DATA = pd.DataFrame(
    [
        ["Arroz largo fino", "Molinos", "Comestibles", 2, 1, 1250, "2026-08-05"],
        ["Leche entera", "La Serenísima", "Comestibles", 1, 0, 1350, "2026-08-11"],
        ["Detergente", "Ala", "Limpieza", 3, 1, 2400, "2026-08-03"],
        ["Jabón para ropa", "Ala", "Limpieza", 0, 1, 3800, "2026-08-15"],
        ["Pollo", "Granja propia", "Carnicería", 2, 0, 6900, "2026-08-09"],
        ["Tomate", "Fresco", "Verdulería", 1, 0, 1800, "2026-08-13"],
        ["Papel higiénico", "Elite", "Hogar", 4, 0, 4200, "2026-07-29"],
        ["Yerba mate", "Rosamonte", "Comestibles", 1, 1, 5100, "2026-08-01"],
        ["Lavandina", "Ayudín", "Limpieza", 2, 0, 1500, "2026-08-07"],
        ["Café", "La Virginia", "Comestibles", 0, 1, 4700, "2026-08-16"],
    ],
    columns=["producto", "marca", "categoria", "stock", "en_uso", "precio", "ultimo_movimiento"],
)


def load_data() -> tuple[pd.DataFrame, bool]:
    candidates = [
        Path("data/stock.csv"),
        Path("data/stock.json"),
        Path(__file__).parents[1] / "data" / "stock.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            if candidate.suffix == ".json":
                data = pd.read_json(candidate)
            else:
                data = pd.read_csv(candidate)
            return normalize_data(data), False
    return DEMO_DATA.copy(), True


def normalize_data(data: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "name": "producto",
        "brand": "marca",
        "category": "categoria",
        "stockQuantity": "stock",
        "inUseCount": "en_uso",
    }
    data = data.rename(columns=aliases).copy()
    defaults = {"marca": "Genérica", "categoria": "Sin categoría", "stock": 0, "en_uso": 0, "precio": 0}
    for column, default in defaults.items():
        if column not in data:
            data[column] = default
    if "producto" not in data:
        data["producto"] = "Producto sin nombre"
    data["stock"] = pd.to_numeric(data["stock"], errors="coerce").fillna(0).astype(int)
    data["en_uso"] = pd.to_numeric(data["en_uso"], errors="coerce").fillna(0).astype(int)
    data["precio"] = pd.to_numeric(data["precio"], errors="coerce").fillna(0)
    return data


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
        .hero { background: linear-gradient(120deg, #163b35 0%, #235c4d 62%, #c6db75 150%); padding: 28px 34px; border-radius: 12px; color: white; margin-bottom: 22px; }
        .hero h1 { color: white; font-size: 2.2rem; margin: 0 0 6px; }
        .hero p { color: #dbe9d7; margin: 0; font-size: 1rem; }
        .metric { background: white; border-left: 4px solid #8ead45; padding: 17px 18px; border-radius: 8px; box-shadow: 0 2px 12px rgba(22,59,53,.07); }
        .metric-label { color: #687771; font-size: .83rem; text-transform: uppercase; letter-spacing: .06em; }
        .metric-value { color: #163b35; font-family: 'Space Grotesk'; font-size: 1.75rem; font-weight: 700; margin-top: 3px; }
        .section-title { color: #163b35; font-family: 'Space Grotesk'; font-size: 1.15rem; font-weight: 700; margin: 22px 0 8px; }
        .stDataFrame { border-radius: 8px; overflow: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric(label: str, value: str) -> None:
    st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)


inject_styles()
data, is_demo = load_data()
data["total"] = data["stock"] + data["en_uso"]
data["estado"] = data["stock"].apply(lambda value: "Crítico" if value <= 1 else "Disponible")

with st.sidebar:
    st.markdown("## Expensas House")
    st.caption("Centro de control del hogar")
    st.divider()
    st.markdown("### Explorar")
    selected_category = st.multiselect("Categorías", sorted(data["categoria"].dropna().unique()), default=[])
    show_critical = st.toggle("Solo stock crítico", value=False)
    st.divider()
    st.markdown("### Asistente de stock")
    question = st.text_input("Buscar producto", placeholder="Ej.: ¿hay leche?")
    if question:
        matches = data[data["producto"].str.contains(question, case=False, na=False)]
        if matches.empty:
            st.info("No encontré ese producto en el inventario.")
        else:
            for _, item in matches.iterrows():
                st.success(f"{item['producto']}: {item['total']} unidad(es) en casa.")

filtered = data.copy()
if selected_category:
    filtered = filtered[filtered["categoria"].isin(selected_category)]
if show_critical:
    filtered = filtered[filtered["stock"] <= 1]

st.markdown(
    '<div class="hero"><h1>Tu casa, en perspectiva</h1><p>Inventario, consumo y decisiones de compra en una sola vista.</p></div>',
    unsafe_allow_html=True,
)
if is_demo:
    st.info("Vista demo activa. Cuando exportes los datos de Room, coloca `stock.csv` o `stock.json` dentro de la carpeta `data/`.")

total_products = int(filtered["total"].sum())
critical_count = int((filtered["stock"] <= 1).sum())
estimated_value = float((filtered["total"] * filtered["precio"]).sum())
categories_count = int(filtered["categoria"].nunique())

metrics = st.columns(4)
with metrics[0]:
    metric("Unidades en casa", f"{total_products}")
with metrics[1]:
    metric("Stock crítico", f"{critical_count}")
with metrics[2]:
    metric("Valor estimado", f"${estimated_value:,.0f}")
with metrics[3]:
    metric("Categorías activas", f"{categories_count}")

left, right = st.columns([1.35, 1])
with left:
    st.markdown('<div class="section-title">Distribución por categoría</div>', unsafe_allow_html=True)
    category_data = filtered.groupby("categoria", as_index=False)["total"].sum().sort_values("total", ascending=False)
    chart = px.bar(category_data, x="total", y="categoria", orientation="h", color="total", color_continuous_scale=["#c6db75", "#235c4d"])
    chart.update_layout(height=320, margin=dict(l=0, r=10, t=10, b=0), showlegend=False, coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(chart, use_container_width=True)
with right:
    st.markdown('<div class="section-title">Estado del inventario</div>', unsafe_allow_html=True)
    status_data = filtered["estado"].value_counts().rename_axis("estado").reset_index(name="cantidad")
    chart = px.pie(status_data, values="cantidad", names="estado", hole=.64, color="estado", color_discrete_map={"Crítico": "#dc6b55", "Disponible": "#8ead45"})
    chart.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-.05))
    st.plotly_chart(chart, use_container_width=True)

st.markdown('<div class="section-title">Productos que requieren atención</div>', unsafe_allow_html=True)
critical = filtered[filtered["stock"] <= 1].sort_values(["stock", "total"])
if critical.empty:
    st.success("No hay productos críticos con los filtros actuales.")
else:
    table = critical[["producto", "marca", "categoria", "stock", "en_uso", "precio"]].rename(
        columns={"producto": "Producto", "marca": "Marca", "categoria": "Categoría", "stock": "Cerradas", "en_uso": "En uso", "precio": "Precio estimado"}
    )
    st.dataframe(table, use_container_width=True, hide_index=True, column_config={"Precio estimado": st.column_config.NumberColumn(format="$%d")})

st.markdown('<div class="section-title">Inventario completo</div>', unsafe_allow_html=True)
st.dataframe(
    filtered[["producto", "marca", "categoria", "stock", "en_uso", "total", "estado"]].rename(
        columns={"producto": "Producto", "marca": "Marca", "categoria": "Categoría", "stock": "Cerradas", "en_uso": "En uso", "total": "Total", "estado": "Estado"}
    ),
    use_container_width=True,
    hide_index=True,
)