import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(layout="wide")
st.title("💸 À Vista vs Parcelado")

st.markdown("---")

# ------------------------------
# Funções comuns
# ------------------------------
def convert_annual_to_monthly_effective(taxa_anual_pct: float) -> float:
    """Converte taxa anual nominal para taxa efetiva mensal (aprox. 30/360)."""
    try:
        return (1 + taxa_anual_pct / 100.0) ** (30.0 / 360.0) - 1.0
    except Exception:
        return 0.0

def valor_presente_data0(fluxo_dict, taxa_mensal):
    """Calcula VP na data 0 para um dicionário {t: fluxo} com taxa mensal efetiva."""
    vp = 0.0
    taxa = taxa_mensal or 0.0
    for t, c in fluxo_dict.items():
        vp += c / ((1 + taxa) ** t)
    return vp

# ------------------------------
# Inicializações de estado (chaves genéricas)
# ------------------------------
st.session_state.setdefault('taxa_anual', 15.0)
st.session_state.setdefault('taxa_anual_slider', 15.0)
st.session_state.setdefault('taxa_mensal_manual', 0.80)
st.session_state.setdefault('taxa_mensal_slider', 0.80)
st.session_state.setdefault('last_changed_taxa_anual', None)
st.session_state.setdefault('last_changed_taxa_mensal', None)

st.session_state.setdefault('last_changed_desconto', None)
st.session_state.setdefault('desconto_pct', 5.0)
st.session_state.setdefault('preco_vista_descontado', None)

# ------------------------------
# Callbacks de sincronização (taxas)
# ------------------------------
def on_change_taxa_anual_input():
    st.session_state['last_changed_taxa_anual'] = 'input'
    st.session_state['taxa_anual_slider'] = float(st.session_state['taxa_anual'])

def on_change_taxa_anual_slider():
    st.session_state['last_changed_taxa_anual'] = 'slider'
    st.session_state['taxa_anual'] = float(st.session_state['taxa_anual_slider'])

def on_change_taxa_mensal_input():
    st.session_state['last_changed_taxa_mensal'] = 'input'
    st.session_state['taxa_mensal_slider'] = float(st.session_state['taxa_mensal_manual'])

def on_change_taxa_mensal_slider():
    st.session_state['last_changed_taxa_mensal'] = 'slider'
    st.session_state['taxa_mensal_manual'] = float(st.session_state['taxa_mensal_slider'])

# ------------------------------
# Callbacks de desconto (percentual ↔ preço à vista descontado)
# ------------------------------
def on_change_desconto_pct():
    st.session_state['last_changed_desconto'] = 'pct'
    preco_orig = float(st.session_state.get('valor_a_vista', 0.0))
    pct = float(st.session_state.get('desconto_pct', 0.0))
    pct = max(0.0, min(100.0, pct))
    preco_desc = preco_orig * (1 - pct / 100.0) if preco_orig > 0 else 0.0
    st.session_state['preco_vista_descontado'] = round(preco_desc, 2)
    st.session_state['desconto_pct'] = round(pct, 4)

def on_change_preco_vista_descontado():
    st.session_state['last_changed_desconto'] = 'preco'
    preco_orig = float(st.session_state.get('valor_a_vista', 0.0))
    preco_desc = float(st.session_state.get('preco_vista_descontado', 0.0))
    preco_desc = max(0.0, preco_desc)
    if preco_orig > 0 and preco_desc > preco_orig:
        preco_desc = preco_orig
    pct = (1 - (preco_desc / preco_orig)) * 100.0 if preco_orig > 0 else 0.0
    pct = max(0.0, min(100.0, pct))
    st.session_state['desconto_pct'] = round(pct, 4)
    st.session_state['preco_vista_descontado'] = round(preco_desc, 2)

# ------------------------------
# Entradas principais
# ------------------------------
st.header("Configurações")

valor_a_vista = st.number_input(
    "Preço do produto (R$)",
    min_value=0.0, value=549.90, step=0.01, format="%.2f", key="valor_a_vista"
)

# Inicializa preço à vista descontado na primeira execução
if st.session_state.get('preco_vista_descontado') is None:
    preco_init = float(valor_a_vista) * (1 - float(st.session_state.get('desconto_pct', 5.0)) / 100.0)
    st.session_state['preco_vista_descontado'] = round(preco_init, 2)

tem_desconto_vista = st.checkbox(
    "Produto possui desconto à vista?",
    value=False, key="tem_desconto_vista"
)

desconto_pct = 0.0
preco_vista_descontado = valor_a_vista
if tem_desconto_vista:
    st.write("Informe o desconto em percentual ou diretamente o preço já descontado. A última alteração domina.")

    desconto_pct = st.number_input(
        "Valor do desconto à vista (%)",
        min_value=0.0, max_value=100.0,
        value=float(st.session_state.get('desconto_pct', 5.0)),
        step=0.01, format="%.4f",
        key="desconto_pct",
        on_change=on_change_desconto_pct
    )

    preco_vista_descontado = st.number_input(
        "Preço à vista (descontado) (R$)",
        min_value=0.0,
        value=float(st.session_state.get('preco_vista_descontado', round(float(valor_a_vista) * (1 - desconto_pct / 100.0), 2))),
        step=0.01, format="%.2f",
        key="preco_vista_descontado",
        on_change=on_change_preco_vista_descontado
    )

    last = st.session_state.get('last_changed_desconto')
    if last == 'preco':
        preco_vista_descontado = float(st.session_state['preco_vista_descontado'])
        desconto_pct = float(st.session_state['desconto_pct'])
    else:
        desconto_pct = float(st.session_state['desconto_pct'])
        preco_vista_descontado = float(st.session_state['preco_vista_descontado'])

    preco_orig = float(valor_a_vista)
    if preco_orig > 0:
        preco_vista_descontado = max(0.0, min(preco_vista_descontado, preco_orig))
        desconto_pct = max(0.0, min(desconto_pct, 100.0))
else:
    desconto_pct = 0.0
    preco_vista_descontado = valor_a_vista

entrada_inicial = st.number_input(
    "Entrada (R$) — se houver",
    min_value=0.0, value=0.0, step=0.01, format="%.2f", key="entrada_inicial"
)

num_prestacoes_max = st.number_input(
    "Número máximo de prestações (limite)",
    min_value=2, max_value=120, value=12, step=1, key="num_prestacoes_max"
)

taxa_opcao = st.selectbox(
    "Tipo da taxa de investimento / juros",
    options=["SELIC (anual)", "CDI (anual)", "Manual (mensal)"],
    key="taxa_opcao"
)

taxa_anual = None
taxa_mensal_manual = None
taxa_mensal_final = 0.0

if taxa_opcao in ["SELIC (anual)", "CDI (anual)"]:
    taxa_anual = st.number_input(
        f"Informe a taxa anual para {taxa_opcao.split()[0]} (%)",
        min_value=0.0, max_value=200.0,
        value=float(st.session_state.get('taxa_anual', 15.0)),
        step=0.01, format="%.4f", key="taxa_anual", on_change=on_change_taxa_anual_input
    )
    taxa_anual_slider = st.slider(
        "Ajuste rápido da taxa anual (%)",
        min_value=0.0, max_value=200.0,
        value=float(st.session_state.get('taxa_anual_slider', float(taxa_anual))),
        step=0.01, key="taxa_anual_slider", on_change=on_change_taxa_anual_slider
    )
    last_ta = st.session_state.get('last_changed_taxa_anual')
    taxa_anual_usada = float(st.session_state['taxa_anual_slider']) if last_ta == 'slider' else float(st.session_state['taxa_anual'])
    # Mantém o ajuste que você vinha usando para SELIC, se for intencional
    if taxa_opcao in ["SELIC (anual)"]:
        taxa_anual_usada -= 0.1
    taxa_mensal_final = convert_annual_to_monthly_effective(taxa_anual_usada)
    taxa_anual = taxa_anual_usada
else:
    taxa_mensal_manual = st.number_input(
        "Informe a taxa mensal efetiva (%)",
        min_value=0.0, max_value=100.0,
        value=float(st.session_state.get('taxa_mensal_manual', 0.80)),
        step=0.01, format="%.4f", key="taxa_mensal_manual", on_change=on_change_taxa_mensal_input
    )
    taxa_mensal_slider = st.slider(
        "Ajuste rápido da taxa mensal (%)",
        min_value=0.0, max_value=100.0,
        value=float(st.session_state.get('taxa_mensal_slider', float(taxa_mensal_manual))),
        step=0.01, key="taxa_mensal_slider", on_change=on_change_taxa_mensal_slider
    )
    last_tm = st.session_state.get('last_changed_taxa_mensal')
    taxa_mensal_percent_usada = float(st.session_state['taxa_mensal_slider']) if last_tm == 'slider' else float(st.session_state['taxa_mensal_manual'])
    taxa_mensal_final = taxa_mensal_percent_usada / 100.0
    taxa_mensal_manual = taxa_mensal_percent_usada

# ------------------------------
# Resumo
# ------------------------------
st.markdown("### Resumo das entradas")
st.write(f"- **Preço do produto:** R$ {valor_a_vista:.2f}")
st.write(f"- **Possui desconto à vista:** {'Sim' if tem_desconto_vista else 'Não'}")
if tem_desconto_vista:
    st.write(f"- **Desconto à vista:** {desconto_pct:.2f} % → Preço à vista com desconto: R$ {preco_vista_descontado:.2f}")
st.write(f"- **Entrada no período 0 (opcional):** R$ {entrada_inicial:.2f}")
st.write(f"- **Número máximo de prestações (limite):** {int(num_prestacoes_max)}")
st.write(f"- **Tipo de taxa selecionada:** {taxa_opcao}")
if taxa_opcao in ["SELIC (anual)", "CDI (anual)"]:
    st.write(f"- **Taxa anual usada:** {taxa_anual:.4f} %")
else:
    st.write(f"- **Taxa mensal usada (manual):** {taxa_mensal_manual:.4f} %")
st.write(f"- **Taxa mensal efetiva usada nas comparações:** {(taxa_mensal_final or 0.0) * 100:.6f} %")

st.markdown("---")

# ------------------------------
# Slider para variar o número de prestações
# ------------------------------
st.subheader("Explorar número de prestações")
n_atual = st.slider(
    "Escolha o número de prestações atual",
    min_value=1,
    max_value=int(num_prestacoes_max),
    value=min(6, int(num_prestacoes_max)),
    step=1,
    key="n_atual"
)

# ------------------------------
# Construção dos fluxos
# ------------------------------
num_periodos = int(n_atual) + 1
fluxo_parcelado = {}
valor_restante = max(0.0, valor_a_vista - entrada_inicial)
parcela_valor = valor_restante / float(n_atual) if n_atual > 0 else 0.0

fluxo_parcelado[0] = float(entrada_inicial)
for t in range(1, num_periodos):
    fluxo_parcelado[t] = parcela_valor

preco_vista_descontado = float(preco_vista_descontado) if tem_desconto_vista else float(valor_a_vista)
fluxo_vista_descontada = {0: float(preco_vista_descontado)}
for t in range(1, num_periodos):
    fluxo_vista_descontada[t] = 0.0

# ------------------------------
# Cálculo dos VPs
# ------------------------------
vp_parcelado_data0 = valor_presente_data0(fluxo_parcelado, taxa_mensal_final)
vp_vista_data0 = valor_presente_data0(fluxo_vista_descontada, taxa_mensal_final)

# ------------------------------
# Gráfico comparativo (menor em vermelho, maior em verde)
# ------------------------------
fig = go.Figure()
offset_x = 0.25
x_parcelado = -offset_x
x_vista = offset_x

color_parc = "red" if vp_parcelado_data0 >= vp_vista_data0 else "green"
fig.add_trace(
    go.Scatter(
        x=[x_parcelado, x_parcelado],
        y=[0, vp_parcelado_data0],
        mode="lines+markers+text",
        line=dict(color=color_parc, width=10),
        marker=dict(size=10, color=color_parc),
        text=[None, f"Parcelado (n={n_atual}): R$ {vp_parcelado_data0:.2f}"],
        textposition="top center",
        name=f"Parcelado (n={n_atual})",
        hoverinfo="text",
        hovertext=[f"Parcelado (n={n_atual}): R$ {vp_parcelado_data0:.2f}"],
    )
)

color_vista = "red" if vp_vista_data0 >= vp_parcelado_data0 else "green"
fig.add_trace(
    go.Scatter(
        x=[x_vista, x_vista],
        y=[0, vp_vista_data0],
        mode="lines+markers+text",
        line=dict(color=color_vista, width=10, dash="dash"),
        marker=dict(size=10, color=color_vista),
        text=[None, f"À vista: R$ {vp_vista_data0:.2f}"],
        textposition="top center",
        name="À vista (com desconto)",
        hoverinfo="text",
        hovertext=[f"À vista (com desconto): R$ {vp_vista_data0:.2f}"],
    )
)

ymin = min(0.0, vp_parcelado_data0, vp_vista_data0)
ymax = max(vp_parcelado_data0, vp_vista_data0)
margem = max(10.0, (ymax - ymin) * 0.15)
fig.update_layout(
    title=f"Comparação de Valor Presente na Data 0 — Parcelado (n={n_atual}) vs À vista",
    xaxis=dict(visible=False, range=[-1, 1]),
    yaxis=dict(title="Valor (R$)", range=[ymin - margem, ymax + margem]),
    height=500,
    margin=dict(l=40, r=40, t=80, b=40),
    showlegend=True,
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# Tabela e sumários
# ------------------------------
st.subheader("Detalhes")
df_rows = []
for t in range(0, num_periodos):
    val_parc = fluxo_parcelado.get(t, 0.0)
    vp_parc_t = val_parc / ((1 + (taxa_mensal_final or 0.0)) ** t)
    val_vista = fluxo_vista_descontada.get(t, 0.0)
    vp_vista_t = val_vista / ((1 + (taxa_mensal_final or 0.0)) ** t)
    df_rows.append(
        {
            "Período": t,
            "Fluxo parcelado (R$)": round(val_parc, 2),
            "VP parcelado na data 0 (R$)": round(vp_parc_t, 2),
            "Fluxo à vista (R$)": round(val_vista, 2),
            "VP à vista na data 0 (R$)": round(vp_vista_t, 2),
        }
    )
df = pd.DataFrame(df_rows)
st.dataframe(df.style.format("{:.2f}"))

st.markdown("---")
st.write(f"Valor Presente parcelado na data 0 com n={n_atual}: **R$ {vp_parcelado_data0:.2f}**")
st.write(f"Valor Presente à vista na data 0: **R$ {vp_vista_data0:.2f}**")
diff = vp_parcelado_data0 - vp_vista_data0
pct = (diff / vp_vista_data0 * 100.0) if vp_vista_data0 != 0 else float('inf')
st.write(f"Diferença (parcelado − à vista): R$ {diff:.2f} ({pct:.2f} %)")

diferenca_preco = valor_a_vista - vp_parcelado_data0
desc_pct = (diferenca_preco / valor_a_vista * 100.0) if valor_a_vista != 0 else float('inf')
st.write(f"Diferença (preço original − VP parcelado): R$ {diferenca_preco:.2f} ({desc_pct:.2f} %)")
