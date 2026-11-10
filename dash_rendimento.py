"""Dashboard 4 — Rendimento do trabalho: média × mediana.
Base própria: dados/rendimento.csv  (indicador: rendimento, em R$)."""
import nucleo as n

TITULO = "Rendimento do trabalho"
ARQUIVO = "rendimento.csv"
PREFIXO = "d4"


def render():
    import plotly.express as px
    import streamlit as st

    st.header(TITULO)
    st.caption("Perspectiva: Renato (Conselho de Indústrias) · A renda “típica” é a média ou "
               "a mediana?")
    df = n.carregar_base(PREFIXO, ARQUIVO, ["rendimento"],
                         "python coletar_dados.py --dashboard rendimento")
    if df is None:
        return
    f = n.filtros(df, PREFIXO)
    if f is None:
        return
    d_base, d, anos, faixa = f
    ref = n.seletor_ano_ref(anos, PREFIXO)
    rend = n.valores_por_uf(d_base, "rendimento", ref)

    st.subheader(f"Histograma do rendimento: média × mediana ({ref})")
    if rend.empty:
        st.info(f"Sem dados de rendimento para {ref}.")
    else:
        rr = n.resumo_estatistico(rend)
        fig = px.histogram(rend.rename("valor").reset_index(), x="valor",
                           nbins=int(min(10, max(3, len(rend)))),
                           labels={"valor": "Rendimento (R$)", "count": "Nº de UFs"})
        fig.update_layout(yaxis_title="Nº de UFs", bargap=0.05)
        pm, pd_ = (("top right", "top left") if rr["media"] >= rr["mediana"]
                   else ("top left", "top right"))
        fig.add_vline(x=rr["media"], line_dash="dash", line_color="red",
                      annotation_text=f"Média R$ {n.fmt(rr['media'], 0)}", annotation_position=pm)
        fig.add_vline(x=rr["mediana"], line_dash="dot", line_color="green",
                      annotation_text=f"Mediana R$ {n.fmt(rr['mediana'], 0)}",
                      annotation_position=pd_)
        st.plotly_chart(fig, use_container_width=True)
        dif = rr["media"] - rr["mediana"]
        assim = rend.skew() if len(rend) >= 3 else float("nan")
        if abs(dif) < 1e-9:
            leitura = "Média e mediana coincidem: distribuição simétrica."
        elif dif > 0:
            leitura = ("**Média acima da mediana → assimetria positiva:** poucas UFs com "
                       "rendimentos altos puxam a média para cima; a mediana representa melhor a UF típica.")
        else:
            leitura = ("**Média abaixo da mediana → assimetria negativa:** poucas UFs com "
                       "rendimentos baixos puxam a média para baixo.")
        st.markdown(f"Média R$ {n.fmt(rr['media'])} · Mediana R$ {n.fmt(rr['mediana'])} · "
                    f"diferença R$ {n.fmt(dif, 2, True)} · assimetria {n.fmt(assim, 2)}. {leitura}")
        st.caption("Cada observação do histograma é uma UF. Vermelha tracejada = média; verde "
                   "pontilhada = mediana.")

    n.painel_serie(rend, "Rendimento médio do trabalho", "R$", PREFIXO, f"— {ref}")

    st.subheader("Evolução do rendimento entre dois anos")
    ano_a, ano_b = n.seletor_anos(anos, PREFIXO)
    comp = n.comparar_anos(d_base, "rendimento", ano_a, ano_b)
    if comp.empty:
        st.info(f"Sem dados de rendimento para {ano_a} e {ano_b}.")
    else:
        n.barras_comparacao(comp, ano_a, ano_b, "Rendimento (R$)")
        st.caption("Variação em R$ (ano final − inicial). Confira se os valores são reais "
                   "(deflacionados) na documentação da tabela do SIDRA.")
        with st.expander("Tabela: rendimento por UF e variação (R$)"):
            st.dataframe(comp.rename(columns={ano_a: f"{ano_a} (R$)", ano_b: f"{ano_b} (R$)",
                                              "variacao_pp": "Variação (R$)"}).round(2),
                         use_container_width=True)

    if "sexo" in d_base.columns and d_base["sexo"].notna().any():
        st.subheader(f"Rendimento médio por sexo ({ref})")
        x = d_base[(d_base["indicador"] == "rendimento") & (d_base["ano"] == ref)
                   & d_base["sexo"].notna()]
        x = x[~x["sexo"].map(lambda v: n._norm(v) == "total")]
        if not x.empty:
            e = x.groupby(["sigla", "sexo"])["valor"].mean().reset_index()
            st.plotly_chart(px.box(e, x="sexo", y="valor", points="all", hover_name="sigla",
                                   labels={"sexo": "Sexo", "valor": "Rendimento (R$)"}),
                            use_container_width=True)

    st.header("Interpretação")
    if not rend.empty:
        st.markdown(f"- Rendimento típico (mediana das UFs): **R$ {n.fmt(rr['mediana'])}**; "
                    f"média **R$ {n.fmt(rr['media'])}**.\n"
                    "- Metas salariais e de renda devem usar a **mediana**, menos sensível a UFs "
                    "de renda muito alta.\n"
                    f"- Maior rendimento: **{rend.idxmax()}** (R$ {n.fmt(rend.max())}); "
                    f"menor: **{rend.idxmin()}** (R$ {n.fmt(rend.min())}).")
    n.fontes()
