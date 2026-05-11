import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="K-Pop Music Intelligence Dashboard",
    layout="wide"
)

st.title("🎵 South Korea Music Intelligence Dashboard")
st.markdown("Momentum • Virality • Trends • Re-Entry Analysis")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)

    # 🔥 IMPORTANT FIX: convert date properly
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    df['is_explicit'] = df['is_explicit'].astype(bool)

    df['song_id'] = df['song'] + "_" + df['artist']

    df = df.sort_values(['song_id', 'date'])

    return df


uploaded_file = st.file_uploader("📂 Upload CSV file", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)
else:
    st.warning("Using default demo dataset")

    df = pd.DataFrame([
        ["2026-01-01", 1, "Demo Song", "BTS", 90, 200000, "single", 1, False]
    ], columns=[
        "date","position","song","artist","popularity",
        "duration_ms","album_type","total_tracks","is_explicit"
    ])

    df['date'] = pd.to_datetime(df['date'])

 

# ---------------- EXTRA BTS DATA (FIXED STRUCTURE) ----------------
extra_data = pd.DataFrame([
    ["2026-01-01", 6, "Dynamite", "BTS", 97, 199000, "single", 1, False],
    ["2026-01-01", 7, "Butter", "BTS", 96, 164000, "single", 1, False],
    ["2026-01-01", 8, "Spring Day", "BTS", 95, 269000, "album", 14, False],
    ["2026-01-01", 9, "IDOL", "BTS", 94, 202000, "album", 11, False],
    ["2026-01-01", 10, "Pink Venom", "BLACKPINK", 93, 180000, "single", 1, False],
    ["2026-01-01", 11, "Hype Boy", "NewJeans", 92, 175000, "single", 1, False],
    ["2026-01-01", 12, "Ditto", "NewJeans", 91, 170000, "single", 1, False],
], columns=[
    "date",
    "position",
    "song",
    "artist",
    "popularity",
    "duration_ms",
    "album_type",
    "total_tracks",
    "is_explicit"
])

df = pd.concat([df, extra_data], ignore_index=True)

# ---------------- FILTERS ----------------
st.sidebar.header("🎛 Filters")

artists = ["All"] + sorted(df['artist'].unique())
artist = st.sidebar.selectbox("Artist", artists)

albums = ["All"] + list(df['album_type'].unique())
album = st.sidebar.selectbox("Album Type", albums)

filtered = df.copy()

if artist != "All":
    filtered = filtered[filtered['artist'] == artist]

if album != "All":
    filtered = filtered[filtered['album_type'] == album]

# ---------------- KPIs ----------------
st.subheader("📊 KPIs")

c1, c2, c3 = st.columns(3)

c1.metric("Songs", filtered['song'].nunique())
c2.metric("Artists", filtered['artist'].nunique())
c3.metric("Avg Popularity", round(filtered['popularity'].mean(), 2))

# ---------------- SONG POPULARITY ----------------
st.subheader("🔥 Song Popularity")

song_pop = filtered.groupby('song')['popularity'].mean().reset_index()

fig1 = px.bar(song_pop, x='song', y='popularity')
st.plotly_chart(fig1, use_container_width=True)

# ---------------- ARTIST RANKING ----------------
st.subheader("🎤 Artist Ranking")

artist_pop = filtered.groupby('artist')['popularity'].mean().reset_index()

fig2 = px.bar(artist_pop.sort_values('popularity', ascending=False),
              x='artist', y='popularity')
st.plotly_chart(fig2, use_container_width=True)

# ---------------- MOMENTUM ----------------
st.subheader("⚡ Momentum Score")

# 🔥 SAFE FIX (ENSURE COLUMN EXISTS)
filtered['song_id'] = filtered['song'] + "_" + filtered['artist']

momentum = filtered.copy()

momentum = momentum.sort_values(['song_id', 'date'])

momentum['prev_position'] = momentum.groupby('song_id')['position'].shift(1)
momentum['rank_change'] = momentum['prev_position'] - momentum['position']

momentum['momentum_score'] = momentum['rank_change'].fillna(0)

top = momentum.groupby(['song', 'artist'])['momentum_score'].mean().reset_index()

fig3 = px.bar(
    top.sort_values('momentum_score', ascending=False).head(10),
    x='song',
    y='momentum_score'
)

st.plotly_chart(fig3, use_container_width=True)

# ---------------- VIRALITY ----------------
st.subheader("🚀 Virality Score")

filtered['virality_score'] = (
    filtered['popularity'] * 0.6 +
    (100 - filtered['position']) * 0.4
)

viral = filtered.groupby('song')['virality_score'].mean().reset_index()

fig4 = px.bar(viral.sort_values('virality_score', ascending=False).head(10),
              x='song', y='virality_score')

st.plotly_chart(fig4, use_container_width=True)

# ---------------- RE-ENTRY (FIXED .dt ERROR) ----------------
st.subheader("🔄 Re-Entry Detection")
st.subheader("🔄 Re-Entry Detection")

filtered['date'] = pd.to_datetime(filtered['date'], errors='coerce')

reentry = []

for song_id, group in filtered.groupby('song_id'):
    group = group.sort_values('date')

    gaps = group['date'].diff().dt.days.fillna(0)

    reentry_count = (gaps > 1).sum()

    reentry.append({
        "song": group['song'].iloc[0],
        "artist": group['artist'].iloc[0],
        "reentry_count": reentry_count
    })

reentry_df = pd.DataFrame(reentry)

st.dataframe(reentry_df.sort_values('reentry_count', ascending=False))

# ---------------- TREND LABEL ----------------
st.subheader("📈 Trend Classification")

momentum['trend'] = momentum['momentum_score'].apply(
    lambda x: "🔥 Viral" if x > 5 else "📈 Rising" if x > 0 else "📉 Declining"
)

st.dataframe(momentum[['song', 'artist', 'momentum_score', 'trend']])

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("🎧 K-Pop Analytics Dashboard | Fully Fixed Version")