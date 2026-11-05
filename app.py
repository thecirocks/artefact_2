"""Site + chat (Streamlit) da Lira, assistente de IA do Empório da Música."""

import base64
import os

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# O agent.py lê o system prompt com caminho relativo, então garantimos
# que o diretório de trabalho seja a raiz do projeto.
os.chdir(BASE_DIR)

TITLE = "Lira - Assistente de IA do Empório da Música"
ICON = os.path.join(BASE_DIR, "assets", "logo_icon.png")
USER_ICON = os.path.join(BASE_DIR, "assets", "user_avatar.png")

st.set_page_config(page_title=TITLE, page_icon=ICON, layout="wide")

# A API key vem de st.secrets (Streamlit Cloud). Ela precisa estar no
# ambiente ANTES de importar agent.py, pois config.py lê a variável e o
# cliente Anthropic é criado no momento do import.
try:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error(
        "ANTHROPIC_API_KEY não encontrada em st.secrets. "
        "Configure em .streamlit/secrets.toml (local) ou nas Secrets do app no Streamlit Cloud."
    )
    st.stop()

from agent import chat  # noqa: E402
from tools.data_loader import DB  # noqa: E402


# ---------------------------------------------------------------------------
# Dados da loja (mesmos do system prompt da Lira)
# ---------------------------------------------------------------------------
STORE = {
    "razao": "Empório da Música Instrumentos Musicais Ltda.",
    "cnpj": "12.345.678/0001-90",
    "endereco": "Rua 14 de Maio, 3200, Centro",
    "cidade": "Campo Grande - MS, 79202-333",
    "telefone": "(67) 3341-4444",
    "whatsapp": "556733414444",
    "email": "contato@emporiodamusica.com.br",
    "suporte": "suporte@emporiodamusica.com.br",
}
MAPS_URL = "https://www.google.com/maps/search/?api=1&query=Rua+14+de+Maio+3200+Centro+Campo+Grande+MS"

# category_id -> imagem em assets/
CATEGORY_IMG = {1: "guitarras", 2: "baixos", 3: "baterias", 4: "teclados", 5: "violoes", 9: "ukuleles"}
# Produtos em destaque (um por categoria)
FEATURED_IDS = [108, 131, 137, 141, 143, 129]

# Rótulo do botão -> mensagem enviada para a Lira
SUGGESTIONS = {
    "Violão para iniciante": "Quero um violão para iniciante",
    "Promoções ativas": "Quais promoções estão ativas?",
    "Acompanhar pedido": "Quero acompanhar meu pedido",
    "Formas de pagamento": "Quais as formas de pagamento?",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
@st.cache_data
def asset_uri(name: str) -> str:
    with open(os.path.join(BASE_DIR, "assets", name), "rb") as f:
        data = base64.b64encode(f.read()).decode()
    mime = "image/svg+xml" if name.endswith(".svg") else "image/png"
    return f"data:{mime};base64,{data}"


def brl(value: float) -> str:
    s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def max_installments(value: float) -> int:
    """Maior parcelamento sem juros respeitando a parcela mínima da loja."""
    for n in range(12, 0, -1):
        minimum = 50 if n <= 3 else 80 if n <= 6 else 100
        if value / n >= minimum:
            return n
    return 1


def html(markup: str) -> None:
    # Em uma linha só, para o Markdown do Streamlit não interpretar a indentação.
    st.markdown(" ".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def available_products():
    p = DB["products"]
    return p[(p["status"] == "active") & (p["stock_quantity"] > 0)]


def active_promos():
    promos = DB["promotions"]
    promos = promos[promos["is_active"] == 1].rename(columns={"description": "campaign"})
    return promos.merge(available_products(), on="product_id")


def price_block(product_id: int, price: float) -> str:
    promo = active_promos()
    promo = promo[promo["product_id"] == product_id]
    if not promo.empty:
        pct = int(promo.iloc[0]["discount_percent"])
        final = price * (1 - pct / 100)
        n = max_installments(final)
        return (f'<div class="old">{brl(price)}</div>'
                f'<div class="price">{brl(final)} <span class="pill">-{pct}%</span></div>'
                f'<div class="inst">ou {n}x de {brl(final / n)} sem juros</div>')
    n = max_installments(price)
    return (f'<div class="price">{brl(price)}</div>'
            f'<div class="inst">ou {n}x de {brl(price / n)} sem juros</div>'
            f'<div class="pix">{brl(price * 0.95)} no PIX (5% off)</div>')


# ---------------------------------------------------------------------------
# Estilo
# ---------------------------------------------------------------------------
html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,700;1,700&display=swap');
:root { --ink:#15110D; --ink2:#231C15; --cream:#F7F1E6; --paper:#FFFDF8; --amber:#E3A23B; --rust:#C2502E; --muted:#7A6C5D; --line:#E6DCCB; }
html, body, [data-testid="stAppViewContainer"] { background: var(--cream); }
[data-testid="stAppViewContainer"] * { font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 4.5rem !important; padding-bottom: 0 !important; max-width: 1080px; }
.em a { text-decoration: none; }
.em h1, .em h2, .em h3 { font-family: 'Playfair Display', Georgia, serif !important; color: var(--ink); margin: 0; padding: 0; letter-spacing: 0; }
.em h1 *, .em h2 *, .em h3 * { font-family: inherit !important; }
.em-topbar { background: var(--ink); color: #D9CBB4; font-size: 13px; padding: 8px 20px; display: flex; flex-wrap: wrap; gap: 6px 22px; justify-content: space-between; border-radius: 0 0 10px 10px; }
.em-topbar a { color: var(--amber); }
.em-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; padding: 18px 4px; }
.em-header img { height: 48px; width: auto; max-width: 100%; }
.em-nav { display: flex; gap: 18px; flex-wrap: wrap; align-items: center; }
.em-nav a { color: var(--ink); font-weight: 600; font-size: 14px; }
.em-nav a:hover { color: var(--rust); }
.em-btn { display: inline-block; background: var(--rust); color: #fff !important; padding: 9px 18px; border-radius: 999px; font-weight: 600; font-size: 14px; }
.em-btn.ghost { background: transparent; border: 1.5px solid var(--amber); color: var(--amber) !important; }
.em-hero { position: relative; border-radius: 18px; overflow: hidden; min-height: 340px; display: flex; align-items: center; background-size: cover; background-position: right center; }
.em-hero .txt { position: relative; padding: 38px 36px; max-width: 500px; }
.em-hero .kicker { color: var(--amber); text-transform: uppercase; letter-spacing: 3px; font-size: 12px; font-weight: 700; }
.em-hero h1 { color: var(--cream) !important; font-size: 36px !important; line-height: 1.15; margin: 10px 0 12px; }
.em-hero h1 em { color: var(--amber); }
.em-hero p { color: #D9CBB4; font-size: 15px; line-height: 1.55; margin-bottom: 26px; }
.em-hero .ctas { display: flex; gap: 12px; flex-wrap: wrap; }
.em-perks { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin: 18px 0 8px; }
.em-perk { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; display: flex; gap: 12px; align-items: center; }
.em-perk .ic { width: 38px; height: 38px; flex: none; border-radius: 50%; background: var(--ink); color: var(--amber); display: grid; place-items: center; font-weight: 700; font-size: 14px; }
.em-perk b { display: block; color: var(--ink); font-size: 14px; }
.em-perk span { color: var(--muted); font-size: 13px; }
.em-sec { margin: 36px 0 14px; display: flex; align-items: end; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.em-sec h2 { font-size: 28px !important; }
.em-sec p { color: var(--muted); margin: 4px 0 0; }
.em-cats { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
.em-cat { position: relative; border-radius: 14px; overflow: hidden; aspect-ratio: 5 / 3; background-size: cover; background-position: center; display: flex; align-items: flex-end; }
.em-cat .lbl { padding: 18px; background: linear-gradient(90deg, rgba(15,12,9,.78), rgba(15,12,9,0)); width: 70%; height: 100%; display: flex; flex-direction: column; justify-content: flex-end; }
.em-cat .ttl { font-family: 'Playfair Display', Georgia, serif !important; color: #fff; font-weight: 700; line-height: 1.2; font-size: 24px; text-shadow: 0 2px 8px rgba(0,0,0,.6); }
.em-cat span { color: var(--amber); font-size: 13px; font-weight: 600; }
.em-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; }
.em-card { background: var(--paper); border: 1px solid var(--line); border-radius: 14px; overflow: hidden; display: flex; flex-direction: column; position: relative; }
.em-card img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; display: block; }
.em-card .body { padding: 14px 16px 18px; display: flex; flex-direction: column; gap: 4px; flex: 1; }
.em-card .cat { color: var(--rust); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; }
.em-card .name { color: var(--ink); font-weight: 600; font-size: 15px; line-height: 1.3; min-height: 40px; }
.em-card .price { color: var(--ink); font-size: 21px; font-weight: 700; margin-top: 6px; }
.em-card .old { color: var(--muted); text-decoration: line-through; font-size: 13px; margin-top: 6px; }
.em-card .inst { color: var(--muted); font-size: 13px; }
.em-card .pix { color: #2F7A55; font-size: 13px; font-weight: 600; }
.em-card .pill { background: var(--rust); color: #fff; font-size: 12px; border-radius: 999px; padding: 2px 8px; vertical-align: middle; }
.em-card .tag { position: absolute; top: 12px; left: 12px; background: var(--ink); color: var(--amber); font-size: 12px; font-weight: 700; padding: 5px 10px; border-radius: 999px; }
.em-lira { background: var(--ink); border-radius: 18px; padding: 28px 30px; margin-bottom: 14px; display: flex; gap: 20px; align-items: center; flex-wrap: wrap; margin-top: 44px; }
.em-lira img { width: 72px; height: 72px; }
.em-lira h2 { color: var(--cream) !important; font-size: 26px !important; }
.em-lira p { color: #D9CBB4; margin: 6px 0 0; max-width: 760px; }
.em-footer { background: var(--ink); color: #D9CBB4; border-radius: 18px 18px 0 0; margin-top: 56px; padding: 40px 34px 0; }
.em-footer .cols { display: grid; grid-template-columns: 1.1fr 1fr 1.3fr 1fr; gap: 28px; }
.em-footer li a { white-space: nowrap; }
@media (max-width: 960px) { .em-footer .cols { grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); } }
.em-footer li { margin-bottom: 6px; }
.em-footer li small { display: block; color: #9C8E7C; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; line-height: 1.4; }
.em-footer img { height: 46px; width: auto; max-width: 100%; }
.em-footer h4 { color: var(--amber); text-transform: uppercase; letter-spacing: 2px; font-size: 13px; margin: 0 0 12px; }
.em-footer p, .em-footer li { font-size: 14px; line-height: 1.7; margin: 0; }
.em-footer ul { list-style: none; padding: 0; margin: 0; }
.em-footer a { color: var(--cream); }
.em-footer .pay { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.em-footer .pay span { border: 1px solid #4A3E31; border-radius: 6px; padding: 4px 10px; font-size: 13px; color: var(--cream); }
.em-footer .bottom { border-top: 1px solid #3A3027; margin-top: 32px; padding: 16px 0 20px; font-size: 12px; color: #9C8E7C; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
/* Chat */
[data-testid="stChatMessage"] { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; }
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stChatMessage"]) { background: #FBF6EC; }
.stButton button { border-radius: 999px; border: 1px solid var(--line); background: var(--paper); color: var(--ink); font-size: 14px; }
.stButton button:hover { border-color: var(--rust); color: var(--rust); }
@media (max-width: 640px) {
  .em-hero { min-height: 0; background-position: 70% center; }
  .em-hero .txt { padding: 30px 22px; background: linear-gradient(90deg, rgba(15,12,9,.85), rgba(15,12,9,.55)); }
  .em-hero h1 { font-size: 28px !important; }
  .em-sec h2 { font-size: 26px !important; }
  .em-nav { gap: 14px; }
  .em-header img { height: 46px; }
}
</style>
""")

# ---------------------------------------------------------------------------
# Topo, header e banner
# ---------------------------------------------------------------------------
html(f"""
<div class="em">
<div class="em-topbar">
<span>Atendimento: <a href="tel:+{STORE['whatsapp']}">{STORE['telefone']}</a> · <a href="https://wa.me/{STORE['whatsapp']}" target="_blank">WhatsApp</a></span>
<span>Frete grátis em Campo Grande para compras acima de R$ 500</span>
<span>Seg a Sex 9h às 18h · Sáb 9h às 13h</span>
</div>
<div class="em-header">
<a href="#inicio"><img src="{asset_uri('logo.svg')}" alt="Empório da Música"></a>
<nav class="em-nav">
<a href="#categorias">Categorias</a><a href="#destaques">Destaques</a><a href="#ofertas">Ofertas</a><a href="#contato">Contato</a>
<a class="em-btn" href="#lira">Fale com a Lira</a>
</nav>
</div>
<div id="inicio" class="em-hero" style="background-image:url('{asset_uri('hero.svg')}')">
<div class="txt">
<div class="kicker">Atendimento com inteligência artificial</div>
<h1>Lira - Assistente de IA do <em>Empório da Música</em></h1>
<p>Tire dúvidas sobre instrumentos, preços, promoções, frete e pedidos a qualquer hora. A Lira conhece todo o nosso catálogo e as condições da loja.</p>
<div class="ctas"><a class="em-btn" href="#lira">Conversar com a Lira</a><a class="em-btn ghost" href="#ofertas">Ver ofertas</a></div>
</div>
</div>
<div class="em-perks">
<div class="em-perk"><div class="ic">12x</div><div><b>Sem juros no cartão</b><span>Todas as bandeiras</span></div></div>
<div class="em-perk"><div class="ic">5%</div><div><b>Desconto no PIX</b><span>Em produtos fora de promoção</span></div></div>
<div class="em-perk"><div class="ic">CG</div><div><b>Frete grátis em Campo Grande</b><span>Acima de R$ 500, em 1 a 3 dias úteis</span></div></div>
<div class="em-perk"><div class="ic">7d</div><div><b>Troca garantida</b><span>Até 7 dias após o recebimento</span></div></div>
</div>
</div>
""")

# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------
products = available_products()
counts = products.groupby("category_id").size()
cat_names = DB["categories"].set_index("category_id")["name"]

cards = ""
for cid, img in CATEGORY_IMG.items():
    n = int(counts.get(cid, 0))
    cards += (f'<div class="em-cat" style="background-image:url(\'{asset_uri(f"cat_{img}.svg")}\')">'
              f'<div class="lbl"><div class="ttl">{cat_names[cid]}</div><span>{n} modelos disponíveis</span></div></div>')

html(f"""
<div class="em" id="categorias">
<div class="em-sec"><div><h2>Categorias</h2><p>Do primeiro instrumento ao equipamento profissional.</p></div></div>
<div class="em-cats">{cards}</div>
</div>
""")

# ---------------------------------------------------------------------------
# Destaques
# ---------------------------------------------------------------------------
cards = ""
for pid in FEATURED_IDS:
    row = products[products["product_id"] == pid]
    if row.empty:
        continue
    r = row.iloc[0]
    img = CATEGORY_IMG.get(int(r["category_id"]), "geral")
    cards += (f'<div class="em-card"><img src="{asset_uri(f"prod_{img}.svg")}" alt="{r["name"]}">'
              f'<div class="body"><div class="cat">{cat_names[r["category_id"]]}</div>'
              f'<div class="name">{r["name"]}</div>{price_block(pid, float(r["price_brl"]))}</div></div>')

html(f"""
<div class="em" id="destaques">
<div class="em-sec"><div><h2>Destaques da loja</h2><p>Instrumentos de referência, com estoque disponível.</p></div></div>
<div class="em-grid">{cards}</div>
</div>
""")

# ---------------------------------------------------------------------------
# Ofertas (promoções ativas)
# ---------------------------------------------------------------------------
promos = active_promos()
if not promos.empty:
    cards = ""
    for _, r in promos.iterrows():
        img = CATEGORY_IMG.get(int(r["category_id"]), "geral")
        cards += (f'<div class="em-card"><span class="tag">{r["campaign"]}</span>'
                  f'<img src="{asset_uri(f"prod_{img}.svg")}" alt="{r["name"]}">'
                  f'<div class="body"><div class="cat">{cat_names[r["category_id"]]}</div>'
                  f'<div class="name">{r["name"]}</div>{price_block(int(r["product_id"]), float(r["price_brl"]))}</div></div>')
    html(f"""
    <div class="em" id="ofertas">
    <div class="em-sec"><div><h2>Ofertas ativas</h2><p>Promoções não cumulativas, válidas enquanto durar o estoque.</p></div></div>
    <div class="em-grid">{cards}</div>
    </div>
    """)

# ---------------------------------------------------------------------------
# Chat com a Lira
# ---------------------------------------------------------------------------
html(f"""
<div class="em" id="lira">
<div class="em-lira">
<img src="{asset_uri('logo_icon.svg')}" alt="Lira">
<div><h2>Converse com a Lira</h2>
<p>Pergunte sobre modelos, preços, estoque, formas de pagamento, frete, trocas ou o status do seu pedido.</p></div>
</div>
</div>
""")

# Histórico usado pela API (inclui tool_use/tool_result) e histórico só para exibição.
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "messages" not in st.session_state:
    st.session_state.messages = []

pending = None
cols = st.columns(len(SUGGESTIONS))
for col, (label, message) in zip(cols, SUGGESTIONS.items()):
    if col.button(label, width="stretch"):
        pending = message

chat_box = st.container(height=460)
with chat_box:
    with st.chat_message("assistant", avatar=ICON):
        st.markdown("Olá! Eu sou a Lira, assistente de IA do Empório da Música. Como posso te ajudar hoje?")
    for msg in st.session_state.messages:
        avatar = ICON if msg["role"] == "assistant" else USER_ICON
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

with st.container():
    prompt = st.chat_input("Digite sua mensagem para a Lira...")
prompt = prompt or pending

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_box:
        with st.chat_message("user", avatar=USER_ICON):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar=ICON):
            history = st.session_state.conversation_history
            history_len = len(history)
            try:
                with st.spinner("A Lira está digitando..."):
                    response = chat(prompt, history)
            except Exception as e:
                print(f"Erro no chat: {e!r}")
                # Desfaz o que chat() já tinha adicionado, para não deixar o histórico inconsistente.
                del history[history_len:]
                st.session_state.messages.pop()
                st.error("Não consegui responder agora. Tente novamente em instantes.")
            else:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# ---------------------------------------------------------------------------
# Rodapé
# ---------------------------------------------------------------------------
html(f"""
<div class="em" id="contato">
<footer class="em-footer">
<div class="cols">
<div>
<img src="{asset_uri('logo_dark.svg')}" alt="Empório da Música">
<p style="margin-top:14px">Loja especializada em instrumentos musicais em Campo Grande/MS desde 2008. Nossa missão é democratizar o acesso a instrumentos de qualidade no Centro-Oeste.</p>
</div>
<div>
<h4>Endereço</h4>
<p>{STORE['endereco']}<br>{STORE['cidade']}</p>
<p style="margin-top:8px"><a href="{MAPS_URL}" target="_blank">Ver no mapa →</a></p>
<h4 style="margin-top:20px">Horário</h4>
<p>Seg a Sex: 9h às 18h<br>Sábado: 9h às 13h<br>Domingos e feriados: fechado</p>
</div>
<div>
<h4>Contato</h4>
<ul>
<li><small>Telefone</small><a href="tel:+{STORE['whatsapp']}">{STORE['telefone']}</a></li>
<li><small>WhatsApp</small><a href="https://wa.me/{STORE['whatsapp']}" target="_blank">{STORE['telefone']}</a></li>
<li><small>E-mail</small><a href="mailto:{STORE['email']}">{STORE['email']}</a></li>
<li><small>Suporte</small><a href="mailto:{STORE['suporte']}">{STORE['suporte']}</a></li>
</ul>
</div>
<div>
<h4>Pagamento</h4>
<div class="pay"><span>PIX</span><span>Crédito 12x</span><span>Débito</span><span>Boleto</span></div>
<h4 style="margin-top:20px">Políticas</h4>
<ul>
<li>Troca e devolução em até 7 dias</li>
<li>Garantia legal de 90 dias</li>
<li>Envio para todo o Brasil com seguro</li>
</ul>
</div>
</div>
<div class="bottom">
<span>© 2026 {STORE['razao']} · CNPJ {STORE['cnpj']}</span>
<span>Dados tratados conforme a LGPD</span>
</div>
</footer>
</div>
""")
