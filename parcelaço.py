import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(layout="wide")
st.title("💸 Comparador Pagamento À Vista vs Parcelado (Protótipo)")

# ------------------------------
# Escolha do modo (Modelo 1 ou Modelo 2)
# ------------------------------
modo = st.selectbox(
    "Escolha o modo de análise",
    options=["Modelo 1 - Valor Presente no tempo", "Modelo 2 - Valor Presente por prestação"],
    key="modo_select"
)
st.markdown("---")

# ------------------------------
# FUNÇÕES COMUNS
# ------------------------------
def convert_annual_to_monthly_effective(taxa_anual_pct):
    try:
        return (1 + taxa_anual_pct / 100.0) ** (30.0 / 360.0) - 1.0
    except Exception:
        return 0.0

def valor_presente(fluxo_dict, taxa_mensal, data_focal=0):
    vp = 0.0
    taxa = taxa_mensal or 0.0
    for t, c in fluxo_dict.items():
        exponent = (t - data_focal)
        vp += c / ((1 + taxa) ** exponent)
    return vp

# ------------------------------
# Preparar session_state para sincronização input <-> slider
# ------------------------------
# Modelo 1
st.session_state.setdefault('last_changed_taxa_anual_m1', None)
st.session_state.setdefault('last_changed_taxa_mensal_m1', None)
st.session_state.setdefault('taxa_anual_m1', 15.0)
st.session_state.setdefault('taxa_anual_slider_m1', 15.0)
st.session_state.setdefault('taxa_mensal_manual_m1', 1.17)
st.session_state.setdefault('taxa_mensal_slider_m1', 1.17)

# Modelo 2
st.session_state.setdefault('last_changed_taxa_anual_m2', None)
st.session_state.setdefault('last_changed_taxa_mensal_m2', None)
st.session_state.setdefault('taxa_anual_m2', 15.0)
st.session_state.setdefault('taxa_anual_slider_m2', 15.0)
st.session_state.setdefault('taxa_mensal_manual_m2', 0.80)
st.session_state.setdefault('taxa_mensal_slider_m2', 0.80)

# Callbacks Modelo 1
def on_change_taxa_anual_input_m1():
    st.session_state['last_changed_taxa_anual_m1'] = 'input'
    st.session_state['taxa_anual_slider_m1'] = float(st.session_state['taxa_anual_m1'])

def on_change_taxa_anual_slider_m1():
    st.session_state['last_changed_taxa_anual_m1'] = 'slider'
    st.session_state['taxa_anual_m1'] = float(st.session_state['taxa_anual_slider_m1'])

def on_change_taxa_mensal_input_m1():
    st.session_state['last_changed_taxa_mensal_m1'] = 'input'
    st.session_state['taxa_mensal_slider_m1'] = float(st.session_state['taxa_mensal_manual_m1'])

def on_change_taxa_mensal_slider_m1():
    st.session_state['last_changed_taxa_mensal_m1'] = 'slider'
    st.session_state['taxa_mensal_manual_m1'] = float(st.session_state['taxa_mensal_slider_m1'])

# Callbacks Modelo 2
def on_change_taxa_anual_input_m2():
    st.session_state['last_changed_taxa_anual_m2'] = 'input'
    st.session_state['taxa_anual_slider_m2'] = float(st.session_state['taxa_anual_m2'])

def on_change_taxa_anual_slider_m2():
    st.session_state['last_changed_taxa_anual_m2'] = 'slider'
    st.session_state['taxa_anual_m2'] = float(st.session_state['taxa_anual_slider_m2'])

def on_change_taxa_mensal_input_m2():
    st.session_state['last_changed_taxa_mensal_m2'] = 'input'
    st.session_state['taxa_mensal_slider_m2'] = float(st.session_state['taxa_mensal_manual_m2'])

def on_change_taxa_mensal_slider_m2():
    st.session_state['last_changed_taxa_mensal_m2'] = 'slider'
    st.session_state['taxa_mensal_manual_m2'] = float(st.session_state['taxa_mensal_slider_m2'])

# ------------------------------
# BLOCO MODELO 1 (mantido com gráficos e HUD originais)
# ------------------------------
if modo.startswith("Modelo 1"):
    st.header("Configurações - Modelo 1")

    # Entradas Modelo 1
    valor_a_vista = st.number_input(
        "Preço do Produto (R$)",
        min_value=0.0, value=549.90, step=0.01, format="%.2f", key="valor_a_vista_m1"
    )

    entrada_inicial = st.number_input(
        "Entrada / pagamento no período 0 (R$) - se houver",
        min_value=0.0, value=0.0, step=0.01, format="%.2f", key="entrada_inicial_m1"
    )

    num_prestacoes = st.number_input(
        "Número de prestações",
        min_value=1, max_value=120, value=6, step=1, key="num_prestacoes_m1"
    )

    tem_desconto_vista = st.checkbox(
        "Produto possui desconto à vista? - Modelo 1",
        value=False, key="tem_desconto_vista_m1"
    )

    desconto_pct = 0.0
    if tem_desconto_vista:
        desconto_pct = st.number_input(
            "Valor do desconto à vista (%) - Modelo 1",
            min_value=0.0, max_value=100.0, value=5.0, step=0.01, format="%.2f", key="desconto_pct_m1"
        )

    taxa_opcao = st.selectbox(
        "Tipo da taxa de investimento / juros",
        options=["SELIC (anual)", "CDI (anual)", "Manual (mensal)"],
        key="taxa_opcao_m1"
    )

    taxa_anual = None
    taxa_mensal_manual = None
    taxa_mensal_final = 0.0

    if taxa_opcao in ["SELIC (anual)", "CDI (anual)"]:
        # number_input and slider kept in sync; last user action decides
        taxa_anual = st.number_input(
            f"Informe a taxa anual para {taxa_opcao.split()[0]} (%)",
            min_value=0.0, max_value=200.0,
            value=float(st.session_state.get('taxa_anual_m1', 15.0)),
            step=0.01, format="%.4f",
            key="taxa_anual_m1", on_change=on_change_taxa_anual_input_m1
        )
        taxa_anual_slider = st.slider(
            "Ajuste rápido da taxa anual (%)",
            min_value=0.0, max_value=200.0,
            value=float(st.session_state.get('taxa_anual_slider_m1', float(taxa_anual))),
            step=0.01, key="taxa_anual_slider_m1", on_change=on_change_taxa_anual_slider_m1
        )
        last = st.session_state.get('last_changed_taxa_anual_m1')
        if last == 'slider':
            taxa_anual_usada = float(st.session_state['taxa_anual_slider_m1'])
        else:
            taxa_anual_usada = float(st.session_state['taxa_anual_m1'])
        taxa_mensal_final = convert_annual_to_monthly_effective(taxa_anual_usada)
        taxa_anual = taxa_anual_usada
    else:
        taxa_mensal_manual = st.number_input(
            "Informe a taxa mensal (%) (valor efetivo por mês)",
            min_value=0.0, max_value=100.0,
            value=float(st.session_state.get('taxa_mensal_manual_m1', 1.17)),
            step=0.01, format="%.4f",
            key="taxa_mensal_manual_m1", on_change=on_change_taxa_mensal_input_m1
        )
        taxa_mensal_slider = st.slider(
            "Ajuste rápido da taxa mensal (%) - Modelo 1",
            min_value=0.0, max_value=100.0,
            value=float(st.session_state.get('taxa_mensal_slider_m1', float(taxa_mensal_manual))),
            step=0.01, key="taxa_mensal_slider_m1", on_change=on_change_taxa_mensal_slider_m1
        )
        last_m = st.session_state.get('last_changed_taxa_mensal_m1')
        if last_m == 'slider':
            taxa_mensal_percent_usada = float(st.session_state['taxa_mensal_slider_m1'])
        else:
            taxa_mensal_percent_usada = float(st.session_state['taxa_mensal_manual_m1'])
        taxa_mensal_final = taxa_mensal_percent_usada / 100.0
        taxa_mensal_manual = taxa_mensal_percent_usada

    # Resumo Modelo 1
    st.markdown("### Resumo das entradas (Modelo 1)")
    st.write(f"- **Valor à vista:** R$ {valor_a_vista:.2f}")
    st.write(f"- **Entrada:** R$ {entrada_inicial:.2f}")
    st.write(f"- **Número de prestações:** {int(num_prestacoes):.0f}")
    st.write(f"- **Possui desconto à vista:** {'Sim' if tem_desconto_vista else 'Não'}")
    if tem_desconto_vista:
        st.write(f"- **Desconto à vista:** {desconto_pct:.2f} % → Preço à vista com desconto: R$ {valor_a_vista * (1 - desconto_pct / 100.0):.2f}")
    st.write(f"- **Tipo de taxa selecionada:** {taxa_opcao}")
    if taxa_opcao in ["SELIC (anual)", "CDI (anual)"]:
        st.write(f"- **Taxa anual usada:** {taxa_anual:.4f} %")
    else:
        st.write(f"- **Taxa mensal usada (manual):** {taxa_mensal_manual:.4f} %")
    st.write(f"- **Taxa mensal efetiva usada nas comparações:** {taxa_mensal_final * 100:.6f} %")

    st.divider()

    # Tratamento dos dados Modelo 1 (mantendo lógica anterior)
    num_periodos = int(num_prestacoes) + 1
    fluxo = {}
    valor_restante = max(0.0, valor_a_vista - entrada_inicial)
    parcela_valor = valor_restante / float(num_prestacoes) if num_prestacoes > 0 else 0.0

    fluxo[0] = float(entrada_inicial)
    for t in range(1, num_periodos):
        fluxo[t] = parcela_valor

    alterar_manual = st.checkbox("Deseja alterar as parcelas manualmente?", value=False, key="alterar_manual_m1")
    if alterar_manual:
        st.subheader("Ajuste opcional dos valores por período")
        for t in range(0, num_periodos):
            key = f"fluxo_manual_m1_{t}"
            valor_manual = st.number_input(f"Período {t}", value=float(fluxo[t]), format="%.2f", key=key)
            fluxo[t] = float(valor_manual)

    # Fluxo vista descontada Modelo 1 (permanecer como pagamento no período 0)
    preco_vista_descontado = valor_a_vista * (1 - (desconto_pct or 0.0) / 100.0)
    fluxo_vista_descontada = {}
    if tem_desconto_vista:
        fluxo_vista_descontada[0] = float(preco_vista_descontado)
        for t in range(1, num_periodos):
            fluxo_vista_descontada[t] = 0.0

    # Plotagem Modelo 1: vetores do VP na data focal selecionada
    def plot_vetores_vp_modelo1(fluxo_dict, taxa_mensal, fluxo_vista_constante):
        data_focal = st.select_slider(
            "Data focal para cálculo do Valor Presente",
            options=list(range(0, num_periodos)),
            value=0,
            key="data_focal_m1"
        )

        vp_principal = valor_presente(fluxo_dict, taxa_mensal, data_focal)
        vp_vista = None
        if fluxo_vista_constante and any(v != 0 for v in fluxo_vista_constante.values()):
            vp_vista = valor_presente(fluxo_vista_constante, taxa_mensal, data_focal)

        fig = go.Figure()
        offset = 0.25 if num_periodos > 3 else 0.15
        x_principal = data_focal - offset if vp_vista is not None else data_focal
        x_vista = data_focal + offset if vp_vista is not None else None

        color_principal = 'green' if vp_principal >= 0 else 'red'
        fig.add_trace(go.Scatter(
            x=[x_principal, x_principal],
            y=[0, vp_principal],
            mode='lines+markers+text',
            line=dict(color=color_principal, width=8),
            marker=dict(size=10, color=color_principal),
            text=[None, f"VP Parcelado: R$ {vp_principal:.2f}"],
            textposition="top center",
            name="Parcelado",
            hoverinfo='text',
            hovertext=[f"VP (parcelas) na data {data_focal}: R$ {vp_principal:.2f}"]
        ))

        valores_para_range = [vp_principal]
        if vp_vista is not None:
            color_vista = 'blue'
            fig.add_trace(go.Scatter(
                x=[x_vista, x_vista],
                y=[0, vp_vista],
                mode='lines+markers+text',
                line=dict(color=color_vista, width=8, dash='dash'),
                marker=dict(size=10, color=color_vista),
                text=[None, f"A Vista: R$ {vp_vista:.2f}"],
                textposition="top center",
                name="A vista",
                hoverinfo='text',
                hovertext=[f"VP a vista com desconto na data {data_focal}: R$ {vp_vista:.2f}"]
            ))
            valores_para_range.append(vp_vista)

        ymin = min(valores_para_range) if valores_para_range else 0.0
        ymax = max(valores_para_range) if valores_para_range else 0.0
        margem_inferior = ymin * 0.02 if ymin != 0 else -1.0
        margem_superior = ymax * 0.05 if ymax != 0 else 1.0
        y0 = ymin - abs(margem_inferior)
        y1 = ymax + abs(margem_superior)

        fig.update_layout(
            title=f"Vetores Valor Presente na Data {data_focal}",
            xaxis=dict(title="Período (referência)", range=[-0.5, max(fluxo_dict.keys()) + 0.5], tickmode='linear'),
            yaxis=dict(title="Valor (R$)", range=[y0, y1]),
            height=600,
            margin=dict(l=40, r=40, t=80, b=40),
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)
        return vp_principal, vp_vista, data_focal

    vp_principal_m1, vp_vista_m1, data_focal_m1 = plot_vetores_vp_modelo1(fluxo, taxa_mensal_final, fluxo_vista_descontada if tem_desconto_vista else None)

    # Tabela e sumários Modelo 1
    st.subheader("Tabela de fluxos e Valores Presentes por período")
    rows = []
    for t in range(0, num_periodos):
        valor_fluxo = fluxo.get(t, 0.0)
        vp_fluxo = valor_fluxo / ((1 + (taxa_mensal_final or 0.0)) ** (t - data_focal_m1))
        row = {
            "Período": t,
            "Fluxo (R$)": round(valor_fluxo, 2),
            f"VP na data {data_focal_m1} (R$)": round(vp_fluxo, 2)
        }
        if tem_desconto_vista:
            valor_vista_const = fluxo_vista_descontada.get(t, 0.0)
            vp_vista_fluxo = valor_vista_const / ((1 + (taxa_mensal_final or 0.0)) ** (t - data_focal_m1))
            row["Valores a vista sem desconto (R$)"] = round(valor_vista_const, 2)
            row[f"Valores a vista com desconto {data_focal_m1} (R$)"] = round(vp_vista_fluxo, 2)
        rows.append(row)
    df = pd.DataFrame(rows)
    st.dataframe(df.style.format("{:.2f}"))

    vp_total = valor_presente(fluxo, taxa_mensal_final, data_focal_m1)
    st.markdown("---")
    st.write(f"Valor Presente parcelado na data {data_focal_m1}: **R$ {vp_total:.2f}**")
    if tem_desconto_vista:
        vp_total_vista = valor_presente(fluxo_vista_descontada, taxa_mensal_final, data_focal_m1)
        st.write(f"Valor Presente a vista com desconto na data {data_focal_m1}: **R$ {vp_total_vista:.2f}**")
        diff = vp_total - vp_total_vista
        pct = (diff / vp_total_vista * 100.0) if vp_total_vista != 0 else float('inf')
        st.write(f"Diferença (parcelado - vista com desconto): R$ {diff:.2f} ({pct:.2f} %)")
        diferenca = (valor_a_vista - vp_total)
        desc = (diferenca / valor_a_vista * 100.0) if valor_a_vista != 0 else float('inf')
        st.write(f'Diferença (Preço original - VP Parcelado): R$ {diferenca:.2f} ({desc:.2f} %)')

# ------------------------------
# BLOCO MODELO 2
# ------------------------------
else:
    st.header("Configurações - Modelo 2 (Valor Presente por prestação)")

    # Entradas solicitadas para Modelo 2
    valor_a_vista2 = st.number_input(
        "Preço do Produto (R$)",
        min_value=0.0, value=549.90, step=0.01, format="%.2f", key="valor_a_vista_m2"
    )

    tem_desconto_vista2 = st.checkbox(
        "Produto possui desconto à vista?",
        value=False, key="tem_desconto_vista_m2"
    )

    desconto_pct2 = 0.0
    if tem_desconto_vista2:
        desconto_pct2 = st.number_input(
            "Valor do desconto à vista (%)",
            min_value=0.0, max_value=100.0, value=5.0, step=0.01, format="%.2f", key="desconto_pct_m2"
        )

    entrada_inicial2 = st.number_input(
        "Entrada (R$) - se houver",
        min_value=0.0, value=0.0, step=0.01, format="%.2f", key="entrada_inicial_m2"
    )

    # Número máximo de prestações (limite para slider)
    num_prestacoes_max2 = st.number_input(
        "Número máximo de prestações (limite)",
        min_value=2, max_value=120, value=12, step=1, key="num_prestacoes_max_m2"
    )

    # Tipo da taxa e entrada dupla (slider + input)
    taxa_opcao2 = st.selectbox(
        "Tipo da taxa de investimento / juros",
        options=["SELIC (anual)", "CDI (anual)", "Manual (mensal)"],
        key="taxa_opcao_m2"
    )

    taxa_anual2 = None
    taxa_mensal_manual2 = None
    taxa_mensal_final2 = 0.0

    if taxa_opcao2 in ["SELIC (anual)", "CDI (anual)"]:
        taxa_anual2 = st.number_input(
            f"Informe a taxa anual para {taxa_opcao2.split()[0]} (%)",
            min_value=0.0, max_value=200.0,
            value=float(st.session_state.get('taxa_anual_m2', 15.0)),
            step=0.01, format="%.4f", key="taxa_anual_m2", on_change=on_change_taxa_anual_input_m2
        )
        taxa_anual_slider2 = st.slider(
            "Ajuste rápido da taxa anual (%)",
            min_value=0.0, max_value=200.0,
            value=float(st.session_state.get('taxa_anual_slider_m2', float(taxa_anual2))),
            step=0.01, key="taxa_anual_slider_m2", on_change=on_change_taxa_anual_slider_m2
        )
        last2 = st.session_state.get('last_changed_taxa_anual_m2')
        if last2 == 'slider':
            taxa_anual_usada2 = float(st.session_state['taxa_anual_slider_m2'])
        else:
            taxa_anual_usada2 = float(st.session_state['taxa_anual_m2'])
        taxa_mensal_final2 = convert_annual_to_monthly_effective(taxa_anual_usada2)
        taxa_anual2 = taxa_anual_usada2
    else:
        taxa_mensal_manual2 = st.number_input(
            "Informe a taxa mensal efetiva (%) - Modelo 2",
            min_value=0.0, max_value=100.0,
            value=float(st.session_state.get('taxa_mensal_manual_m2', 0.80)),
            step=0.01, format="%.4f", key="taxa_mensal_manual_m2", on_change=on_change_taxa_mensal_input_m2
        )
        taxa_mensal_slider2 = st.slider(
            "Ajuste rápido da taxa mensal (%) - Modelo 2",
            min_value=0.0, max_value=100.0,
            value=float(st.session_state.get('taxa_mensal_slider_m2', float(taxa_mensal_manual2))),
            step=0.01, key="taxa_mensal_slider_m2", on_change=on_change_taxa_mensal_slider_m2
        )
        last_m2 = st.session_state.get('last_changed_taxa_mensal_m2')
        if last_m2 == 'slider':
            taxa_mensal_percent_usada2 = float(st.session_state['taxa_mensal_slider_m2'])
        else:
            taxa_mensal_percent_usada2 = float(st.session_state['taxa_mensal_manual_m2'])
        taxa_mensal_final2 = taxa_mensal_percent_usada2 / 100.0
        taxa_mensal_manual2 = taxa_mensal_percent_usada2

    # Resumo Modelo 2
    st.markdown("### Resumo das entradas")
    st.write(f"- **Preço do Produto:** R$ {valor_a_vista2:.2f}")
    st.write(f"- **Possui desconto à vista:** {'Sim' if tem_desconto_vista2 else 'Não'}")
    if tem_desconto_vista2:
        st.write(f"- **Desconto à vista:** {desconto_pct2:.2f} % → Preço à vista com desconto: R$ {valor_a_vista2 * (1 - desconto_pct2 / 100.0):.2f}")
    st.write(f"- **Entrada no período 0 (opcional):** R$ {entrada_inicial2:.2f}")
    st.write(f"- **Número máximo de prestações (limite):** {int(num_prestacoes_max2)}")
    st.write(f"- **Tipo de taxa selecionada:** {taxa_opcao2}")
    if taxa_opcao2 in ["SELIC (anual)", "CDI (anual)"]:
        st.write(f"- **Taxa anual usada:** {taxa_anual2:.4f} %")
    else:
        st.write(f"- **Taxa mensal usada (manual):** {taxa_mensal_manual2:.4f} %")
    st.write(f"- **Taxa mensal efetiva usada nas comparações (Modelo 2):** {(taxa_mensal_final2 or 0.0) * 100:.6f} %")

    st.markdown("---")

    # Slider interativo que varia o número de prestações (n atual)
    st.subheader("Explorar Número de Prestações")
    n_atual = st.slider(
        "Escolha o número de prestações atual",
        min_value=1,
        max_value=int(num_prestacoes_max2),
        value=min(6, int(num_prestacoes_max2)),
        step=1,
        key="n_atual_m2"
    )

    # Cálculos Modelo 2
    num_periodos_2 = int(n_atual) + 1
    fluxo_parcelado_2 = {}
    valor_restante2 = max(0.0, valor_a_vista2 - entrada_inicial2)
    parcela_valor2 = valor_restante2 / float(n_atual) if n_atual > 0 else 0.0

    fluxo_parcelado_2[0] = float(entrada_inicial2)
    for t in range(1, num_periodos_2):
        fluxo_parcelado_2[t] = parcela_valor2

    if tem_desconto_vista2:
        preco_vista_descontado2 = valor_a_vista2 * (1 - desconto_pct2 / 100.0)
    else:
        preco_vista_descontado2 = valor_a_vista2

    fluxo_vista_descontada_2 = {0: float(preco_vista_descontado2)}
    for t in range(1, num_periodos_2):
        fluxo_vista_descontada_2[t] = 0.0

    def valor_presente_data0(fluxo_dict, taxa_mensal):
        vp = 0.0
        taxa = taxa_mensal or 0.0
        for t, c in fluxo_dict.items():
            vp += c / ((1 + taxa) ** t)
        return vp

    vp_parcelado_data0 = valor_presente_data0(fluxo_parcelado_2, taxa_mensal_final2)
    vp_vista_data0 = valor_presente_data0(fluxo_vista_descontada_2, taxa_mensal_final2)

    # Gráfico Modelo 2: apenas dois vetores VP (parcelado vs vista com desconto)
    fig = go.Figure()
    offset_x = 0.25
    x_parcelado = -offset_x
    x_vista = offset_x

    color_parc = "green" if vp_parcelado_data0 >= 0 else "red"
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

    color_vista = "blue"
    fig.add_trace(
        go.Scatter(
            x=[x_vista, x_vista],
            y=[0, vp_vista_data0],
            mode="lines+markers+text",
            line=dict(color=color_vista, width=10, dash="dash"),
            marker=dict(size=10, color=color_vista),
            text=[None, f"A Vista: R$ {vp_vista_data0:.2f}"],
            textposition="top center",
            name="A Vista (com desconto)",
            hoverinfo="text",
            hovertext=[f"A Vista (com desconto): R$ {vp_vista_data0:.2f}"],
        )
    )

    ymin = min(0.0, vp_parcelado_data0, vp_vista_data0)
    ymax = max(vp_parcelado_data0, vp_vista_data0)
    margem = max(10.0, (ymax - ymin) * 0.15)
    fig.update_layout(
        title=f"Comparação VP na Data 0 — Parcelado (n={n_atual}) vs Vista (com desconto)",
        xaxis=dict(visible=False, range=[-1, 1]),
        yaxis=dict(title="Valor (R$)", range=[ymin - margem, ymax + margem]),
        height=500,
        margin=dict(l=40, r=40, t=80, b=40),
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabela e sumários Modelo 2
    st.subheader("Detalhes")
    df_rows = []
    for t in range(0, num_periodos_2):
        val_parc = fluxo_parcelado_2.get(t, 0.0)
        vp_parc_t = val_parc / ((1 + (taxa_mensal_final2 or 0.0)) ** t)
        val_vista = fluxo_vista_descontada_2.get(t, 0.0)
        vp_vista_t = val_vista / ((1 + (taxa_mensal_final2 or 0.0)) ** t)
        df_rows.append(
            {
                "Período": t,
                "Fluxo Parcelado (R$)": round(val_parc, 2),
                f"VP Parcelado na Data 0 (R$)": round(vp_parc_t, 2),
                "Fluxo Vista (R$)": round(val_vista, 2),
                f"VP Vista na Data 0 (R$)": round(vp_vista_t, 2),
            }
        )
    df2 = pd.DataFrame(df_rows)
    st.dataframe(df2.style.format("{:.2f}"))

    st.markdown("---")
    st.write(f"Valor Presente Parcelado na Data 0 com n={n_atual}: **R$ {vp_parcelado_data0:.2f}**")
    st.write(f"Valor Presente a vista com desconto na Data 0: **R$ {vp_vista_data0:.2f}**")
    diff2 = vp_parcelado_data0 - vp_vista_data0
    pct2 = (diff2 / vp_vista_data0 * 100.0) if vp_vista_data0 != 0 else float("inf")
    st.write(f"Diferença (parcelado - vista): R$ {diff2:.2f} ({pct2:.2f} %)")
    diferenca2 = valor_a_vista2 - vp_parcelado_data0
    desc2 = (diferenca2 / valor_a_vista2 * 100.0) if valor_a_vista2 != 0 else float("inf")
    st.write(f"Diferença (preço original - VP parcelado): R$ {diferenca2:.2f} ({desc2:.2f} %)")
