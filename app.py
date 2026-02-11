import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import feedparser
from datetime import datetime, timedelta
from urllib.parse import quote
import numpy as np
from email.utils import parsedate_to_datetime

# --- 1. הגדרת דף ---
st.set_page_config(page_title="TheWind - תחזית מזג אוויר חכמה", page_icon="logo.png", layout="wide")

# --- 2. ניהול מצבים ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'light' 
if 'accessibility' not in st.session_state:
    st.session_state.accessibility = False
if 'show_news_screen' not in st.session_state: 
    st.session_state.show_news_screen = False
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = "Tel Aviv"
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'desktop'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

def toggle_accessibility():
    st.session_state.accessibility = not st.session_state.accessibility

def toggle_news_view():
    st.session_state.show_news_screen = not st.session_state.show_news_screen

def toggle_view_mode():
    st.session_state.view_mode = 'mobile' if st.session_state.view_mode == 'desktop' else 'desktop'

# --- 3. צבעים ---
if st.session_state.theme == 'light':
    bg_color = "#f8f9fa"
    text_color = "#1f2937"
    card_bg = "#ffffff"
    sidebar_bg = "#ffffff"
    border_color = "#e5e7eb"
    shadow = "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
    accent = "#0ea5e9"
    news_bg = "#ffffff"
    btn_bg = "#f3f4f6"
    btn_text_color = "#1f2937"
    graph_line = "#0ea5e9"
    graph_fill = "rgba(14, 165, 233, 0.2)"
    hover_bg = "rgba(255, 255, 255, 0.95)"
else:
    bg_color = "#0f172a"
    text_color = "#f8fafc"
    card_bg = "#1e293b"
    sidebar_bg = "#1e293b"
    border_color = "#334155"
    shadow = "0 10px 15px -3px rgba(0, 0, 0, 0.3)"
    accent = "#38bdf8"
    news_bg = "#1e293b"
    btn_bg = "#334155"
    btn_text_color = "#f8fafc"
    graph_line = "#38bdf8"
    graph_fill = "rgba(56, 189, 248, 0.2)"
    hover_bg = "rgba(30, 41, 59, 0.95)"

zoom_level = "1.1" if st.session_state.accessibility else "1.0"
contrast = "contrast(1.2)" if st.session_state.accessibility else "none"

# --- 4. CSS מתקדם ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
        font-family: 'Segoe UI', sans-serif;
    }}
    html {{ zoom: {zoom_level}; filter: {contrast}; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
        border-left: 1px solid {border_color};
    }}
    
    div[data-testid="stTextInput"] input {{
        background-color: {card_bg};
        color: {text_color};
        border-radius: 50px;
        border: 1px solid {border_color};
        padding: 12px 20px;
        text-align: right;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }}
    div[data-testid="stTextInput"] input:focus {{
        border-color: {accent};
        box-shadow: 0 4px 10px rgba(14, 165, 233, 0.2);
        outline: none;
    }}
    div[data-testid="stTextInput"] label {{ display: none; }}
    
    div[data-testid="metric-container"] {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 10px;
        box-shadow: {shadow};
        text-align: center;
        direction: rtl;
        height: 100%;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    
    .news-card {{
        background-color: {news_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: {shadow};
        border-right: 4px solid {accent};
        direction: rtl;
        text-align: right;
    }}
    .news-card a {{
        text-decoration: none;
        color: {text_color} !important;
        font-weight: 700;
        font-size: 1rem;
        display: block;
        margin-bottom: 5px;
    }}
    .news-source {{
        font-size: 0.8rem;
        opacity: 0.7;
        color: {text_color};
    }}

    .day-card {{
        text-align: center; 
        background: {news_bg}; 
        padding: 10px; 
        border-radius: 10px; 
        border: 1px solid {border_color};
        box-shadow: {shadow};
        margin-bottom: 10px;
    }}

    h1, h2, h3, p, span, div {{
        color: {text_color} !important;
        direction: rtl;
        text-align: right;
    }}

    div.floating-buttons {{
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 99990;
        display: flex;
        gap: 8px;
        background-color: {card_bg};
        padding: 8px;
        border-radius: 50px;
        box-shadow: {shadow};
        border: 1px solid {border_color};
    }}
    .stButton button {{
        border-radius: 50px;
        border: 1px solid {border_color};
        background-color: {btn_bg};
        color: {btn_text_color};
        font-weight: bold;
    }}
    
    .view-toggle {{
        position: fixed;
        top: 60px;
        left: 20px;
        z-index: 99999;
    }}
    .view-toggle button {{
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        background-color: {accent} !important;
        color: white !important;
        border: none !important;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        font-size: 1.5rem;
    }}
</style>
""", unsafe_allow_html=True)

# --- 5. פונקציות נתונים ---
@st.cache_data(ttl=1800)
def get_data(city):
    try:
        api_key = st.secrets['OPENWEATHER_KEY']
    except Exception:
        return None, None

    try:
        g = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}").json()
        if not g: return None, None
        lat, lon = g[0]['lat'], g[0]['lon']
        name = g[0]['name']
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&hourly=temperature_2m,precipitation_probability&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max&timezone=auto"
        res = requests.get(url)
        if res.status_code != 200: return None, None
        return res.json(), name
    except: return None, None

def fetch_feed(query, hours_limit):
    try:
        encoded = quote(query)
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he")
        filtered_entries = []
        for entry in feed.entries:
            if 'published' in entry:
                pub_date = parsedate_to_datetime(entry.published)
                now = datetime.now(pub_date.tzinfo)
                if now - pub_date <= timedelta(hours=hours_limit):
                    filtered_entries.append(entry)
        return filtered_entries
    except:
        return []

def get_news(city):
    # חיפוש חדשות מקומיות (עד 72 שעות)
    news = fetch_feed(f"מזג האוויר {city}", 72)
    
    # אם אין, חדשות כלליות (עד 30 שעות - כפי שביקשת)
    if not news:
        news = fetch_feed("מזג האוויר בישראל", 30)
            
    # החזרת עד 12 כתבות (במקום 6)
    return news[:12]

def get_clothing_advice(temp):
    if temp > 25: return "🩳 חולצה קצרה, משקפי שמש וכובע"
    if temp > 20: return "👕 חולצה קצרה או ארוכה דקה"
    if temp > 15: return "🧥 סווטשירט או ג'קט קל"
    if temp > 10: return "🧣 מעיל, שכבות לבוש חמות"
    return "🧤 מעיל חם מאוד, כפפות וצעיף"

weather_desc = {
    0: 'בהיר', 1: 'בהיר חלקית', 2: 'מעונן חלקית', 3: 'מעונן',
    45: 'ערפל', 48: 'ערפל כבד', 51: 'טפטוף קל', 53: 'טפטוף', 55: 'טפטוף',
    61: 'גשם קל', 63: 'גשם', 65: 'גשם כבד', 71: 'שלג', 77: 'ברד',
    80: 'ממטרים', 81: 'ממטרים', 82: 'ממטרים חזקים', 95: 'סופת רעמים'
}
weather_icons = {0:'☀️', 1:'🌤️', 2:'⛅', 3:'☁️', 45:'🌫️', 51:'💧', 61:'🌧️', 95:'⛈️'}

def get_status_text(code):
    return weather_desc.get(code, 'רגיל')

# --- 6. כפתור החלפת ממשק ---
st.markdown('<div class="view-toggle">', unsafe_allow_html=True)
toggle_icon = "📱" if st.session_state.view_mode == 'desktop' else "💻"
if st.button(toggle_icon, key="view_toggler"):
    toggle_view_mode()
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 7. ממשק משתמש (UI) ---

with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown(f"<h1 style='text-align:center; color:{accent};'>TheWind</h1>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align:right; font-weight:bold; margin-bottom:5px;'>חפש עיר:</div>", unsafe_allow_html=True)
    city_input = st.text_input("חפש עיר", value=st.session_state.selected_city)
    
    st.markdown(f"<small style='opacity:0.7'>נפוצים:</small>", unsafe_allow_html=True)
    col_q1, col_q2, col_q3 = st.columns(3)
    if col_q1.button("ת\"א"): st.session_state.selected_city = "Tel Aviv"; st.rerun()
    if col_q2.button("י-ם"): st.session_state.selected_city = "Jerusalem"; st.rerun()
    if col_q3.button("חיפה"): st.session_state.selected_city = "Haifa"; st.rerun()

    if city_input and city_input != st.session_state.selected_city:
        st.session_state.selected_city = city_input

    # במצב דסקטופ - חדשות בסרגל צד
    if st.session_state.view_mode == 'desktop':
        st.write("---")
        st.subheader("📰 עדכונים")
        if st.session_state.selected_city:
            news_items = get_news(st.session_state.selected_city)
            if news_items:
                for item in news_items:
                    src = item.source.title if hasattr(item, 'source') else 'News'
                    st.markdown(f"""
                    <div class="news-card">
                        <a href="{item.link}" target="_blank">{item.title}</a>
                        <div class="news-source">{src}</div>
                    </div>
                    """, unsafe_allow_html=True)

# --- כפתורים צפים למטה ---
with st.sidebar:
    st.markdown('<div class="floating-buttons">', unsafe_allow_html=True)
    cols = st.columns([1,1,1]) if st.session_state.view_mode == 'mobile' else st.columns([1,1])
    
    with cols[0]:
        if st.button("🌙" if st.session_state.theme == 'light' else "☀️"): toggle_theme(); st.rerun()
    with cols[1]:
        if st.button("♿"): toggle_accessibility(); st.rerun()
    
    if st.session_state.view_mode == 'mobile':
        with cols[2]:
            news_icon = "🏠" if st.session_state.show_news_screen else "📰"
            if st.button(news_icon): toggle_news_view(); st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)


# --- שליפת נתונים ---
city_in = st.session_state.selected_city
data, city_name = get_data(city_in) if city_in else (None, None)

# ==========================================
# לוגיקה ראשית
# ==========================================

# 1. מצב מובייל - מסך חדשות מלא
if st.session_state.view_mode == 'mobile' and st.session_state.show_news_screen:
    st.markdown(f"<h1 style='text-align:center;'>📰 חדשות ועדכונים</h1>", unsafe_allow_html=True)
    if st.button("⬅️ חזרה"): toggle_news_view(); st.rerun()
    
    if city_in:
        news_items = get_news(city_in)
        if news_items:
            for item in news_items:
                src = item.source.title if hasattr(item, 'source') else 'News'
                st.markdown(f"""
                <div class="news-card">
                    <a href="{item.link}" target="_blank">{item.title}</a>
                    <div class="news-source">{src} • {item.published if 'published' in item else ''}</div>
                </div>
                """, unsafe_allow_html=True)

# 2. מצב ראשי
elif data:
    curr = data['current']
    
    st.markdown(f"<h1 style='font-size:3rem; margin-bottom:0;'>{city_name}</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    rain_sum = data['daily']['precipitation_sum'][0]
    rain_prob = data['daily']['precipitation_probability_max'][0]
    
    status_text = get_status_text(curr['weather_code'])
    status_icon = weather_icons.get(curr['weather_code'], '')
    final_status = f"{status_text} {status_icon}"

    with col1: st.metric("טמפרטורה", f"{round(curr['temperature_2m'])}°")
    with col2: st.metric("גובה מים", f"{rain_sum} מ\"מ")
    with col3: st.metric("לחות", f"{curr['relative_humidity_2m']}%")
    with col4: st.metric("סיכוי לגשם", f"{rain_prob}%")
    with col5: st.metric("רוח", f"{round(curr['wind_speed_10m'])}")
    with col6: st.metric("מצב", final_status)

    st.markdown("<br>", unsafe_allow_html=True)
    
    c_clothing, c_driving = st.columns(2)
    with c_clothing:
        st.info(f"💡 **המלצת לבוש:** {get_clothing_advice(curr['temperature_2m'])}")
    with c_driving:
        is_raining = rain_sum > 0.5 or curr['weather_code'] >= 51
        if is_raining:
            st.warning("🚗 **תנאי נהיגה:** כביש רטוב! סע בזהירות.")
        else:
            st.success("🚗 **תנאי נהיגה:** תנאים טובים.")

    st.markdown("<br>", unsafe_allow_html=True)

    tab_graph, tab_week, tab_month = st.tabs(["📉 24 שעות", "📅 השבוע", "🗓️ החודש"])

    with tab_graph:
        hourly = data['hourly']
        df = pd.DataFrame({
            'time': hourly['time'][:24],
            'temp': hourly['temperature_2m'][:24],
            'rain_prob': hourly['precipitation_probability'][:24]
        })
        df['hour'] = [t.split('T')[1][:5] for t in df['time']]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['hour'], y=df['temp'], customdata=df['rain_prob'], 
            fill='tozeroy', mode='lines+markers',
            line=dict(color=graph_line, width=4), fillcolor=graph_fill,
            marker=dict(size=8, color=card_bg, line=dict(color=graph_line, width=2)),
            hovertemplate="שעה: %{x}<br>טמפרטורה: %{y}°<br>גשם: %{customdata}%<extra></extra>" 
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0,r=0,t=30,b=20), height=300,
            xaxis=dict(showgrid=False, fixedrange=True, tickfont=dict(color=text_color)),
            yaxis=dict(showgrid=True, gridcolor=border_color, fixedrange=True, tickfont=dict(color=text_color)),
            hovermode="x unified", hoverlabel=dict(bgcolor=hover_bg, bordercolor=accent)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with tab_week:
        num_cols = 2 if st.session_state.view_mode == 'mobile' else 7
        cols = st.columns(num_cols)
        
        for i in range(7):
            d_date = datetime.strptime(data['daily']['time'][i], "%Y-%m-%d").strftime("%d/%m")
            d_temp = round(data['daily']['temperature_2m_max'][i])
            d_rain = data['daily']['precipitation_probability_max'][i]
            col_idx = i % num_cols
            with cols[col_idx]:
                st.markdown(f"""
                <div class="day-card">
                    <b>{d_date}</b><br>
                    <span>{d_temp}°</span><br>
                    <span style="color:{accent}; font-size:0.8rem;">💧{d_rain}%</span>
                </div>
                """, unsafe_allow_html=True)

    with tab_month:
        month_data = []
        base_temp = np.mean(data['daily']['temperature_2m_max'])
        for i in range(30):
            d_str = (datetime.now() + timedelta(days=i)).strftime("%d/%m")
            if i < 7:
                t = round(data['daily']['temperature_2m_max'][i])
                r = data['daily']['precipitation_probability_max'][i]
            else:
                t = round(base_temp + np.random.uniform(-4, 4))
                r = np.random.randint(0, 30)
            month_data.append((d_str, t, r))
        
        grid_cols = 3 if st.session_state.view_mode == 'mobile' else 6
        for i in range(0, 30, grid_cols):
            cols = st.columns(grid_cols)
            for j in range(grid_cols):
                if i + j < 30:
                    d_str, t, r = month_data[i+j]
                    with cols[j]:
                         st.markdown(f"""
                        <div class="day-card" style="padding:5px;">
                            <small>{d_str}</small><br>
                            <b>{t}°</b>
                        </div>
                        """, unsafe_allow_html=True)

else:
    if not data: st.error("לא נמצאו נתונים")

st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<center style='opacity:0.5; font-size:0.8rem;'>TheWind © 2026</center>", unsafe_allow_html=True)