import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="K-Pop Momentum Analytics",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("🎵 South Korea Top 50 Analytics Dashboard")
st.markdown("Comeback Momentum, Re-Entry & Fandom Intensity Analysis")

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("south_korea_top50.csv")

    # Convert date
    df['date'] = pd.to_datetime(df['date'])

    # Song ID
    df['song_id'] = (
        df['song'].str.lower()
        + "_"
        + df['artist'].str.lower()
    )

    # Duration in minutes
    if 'duration_ms' in df.columns:
        df['duration_min'] = df['duration_ms'] / 60000

    return df

df = load_data()

# ---------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------

st.sidebar.header("Filters")

artist_list = sorted(df['artist'].unique())

selected_artist = st.sidebar.selectbox(
    "Select Artist",
    ["All"] + artist_list
)

album_filter = st.sidebar.selectbox(
    "Album Type",
    ["All"] + list(df['album_type'].unique())
)

# Apply filters
filtered_df = df.copy()

if selected_artist != "All":
    filtered_df = filtered_df[
        filtered_df['artist'] == selected_artist
    ]

if album_filter != "All":
    filtered_df = filtered_df[
        filtered_df['album_type'] == album_filter
    ]

# ---------------------------------------------------
# KPI SECTION
# ---------------------------------------------------

st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Songs",
        filtered_df['song'].nunique()
    )

with col2:
    st.metric(
        "Total Artists",
        filtered_df['artist'].nunique()
    )

with col3:
    st.metric(
        "Average Popularity",
        round(filtered_df['popularity'].mean(), 2)
    )

with col4:
    st.metric(
        "Highest Popularity",
        filtered_df['popularity'].max()
    )

# ---------------------------------------------------
# DATA PREVIEW
# ---------------------------------------------------

st.subheader("🎧 Dataset Preview")

st.dataframe(filtered_df)

# ---------------------------------------------------
# SONG POPULARITY CHART
# ---------------------------------------------------

st.subheader("🔥 Song Popularity")

song_popularity = (
    filtered_df.groupby(['song', 'artist'])['popularity']
    .mean()
    .reset_index()
)

fig1 = px.bar(
    song_popularity,
    x='song',
    y='popularity',
    color='artist',
    title='Average Song Popularity'
)

st.plotly_chart(fig1, use_container_width=True)

# ---------------------------------------------------
# ARTIST POPULARITY
# ---------------------------------------------------

st.subheader("🎤 Artist Popularity Ranking")

artist_popularity = (
    filtered_df.groupby('artist')['popularity']
    .mean()
    .reset_index()
    .sort_values(by='popularity', ascending=False)
)

fig2 = px.bar(
    artist_popularity,
    x='artist',
    y='popularity',
    color='artist',
    title='Artist Popularity'
)

st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------
# EXPLICIT VS CLEAN CONTENT
# ---------------------------------------------------

st.subheader("🚫 Explicit vs Clean Songs")

explicit_df = (
    filtered_df['is_explicit']
    .value_counts()
    .reset_index()
)

explicit_df.columns = ['Explicit', 'Count']

fig3 = px.pie(
    explicit_df,
    names='Explicit',
    values='Count',
    title='Explicit Content Distribution'
)

st.plotly_chart(fig3, use_container_width=True)

# ---------------------------------------------------
# ALBUM TYPE ANALYSIS
# ---------------------------------------------------

st.subheader("💿 Album Type Analysis")

album_df = (
    filtered_df.groupby('album_type')['popularity']
    .mean()
    .reset_index()
)

fig4 = px.bar(
    album_df,
    x='album_type',
    y='popularity',
    color='album_type',
    title='Album Type vs Popularity'
)

st.plotly_chart(fig4, use_container_width=True)

# ---------------------------------------------------
# DAILY RANK MOVEMENT
# ---------------------------------------------------

st.subheader("📈 Daily Rank Movement")

rank_df = filtered_df.sort_values('date')

fig5 = px.line(
    rank_df,
    x='date',
    y='position',
    color='song',
    markers=True,
    title='Song Rank Over Time'
)

fig5.update_yaxes(autorange="reversed")

st.plotly_chart(fig5, use_container_width=True)

# ---------------------------------------------------
# RE-ENTRY DETECTION
# ---------------------------------------------------

st.subheader("🔄 Re-Entry Detection")

reentry_results = []

for song_id, group in filtered_df.groupby('song_id'):

    group = group.sort_values('date')

    dates = list(group['date'])

    reentry_count = 0

    for i in range(1, len(dates)):

        gap = (dates[i] - dates[i - 1]).days

        if gap > 1:
            reentry_count += 1

    reentry_results.append({
        'song_id': song_id,
        'song': group['song'].iloc[0],
        'artist': group['artist'].iloc[0],
        'reentry_count': reentry_count
    })

reentry_df = pd.DataFrame(reentry_results)

st.dataframe(
    reentry_df.sort_values(
        by='reentry_count',
        ascending=False
    )
)

# ---------------------------------------------------
# MOMENTUM SCORE
# ---------------------------------------------------

st.subheader("⚡ Momentum Analysis")

momentum_df = filtered_df.copy()

momentum_df = momentum_df.sort_values(
    ['song_id', 'date']
)

momentum_df['previous_position'] = (
    momentum_df.groupby('song_id')['position']
    .shift(1)
)

momentum_df['rank_jump'] = (
    momentum_df['previous_position']
    - momentum_df['position']
)

momentum_df['previous_popularity'] = (
    momentum_df.groupby('song_id')['popularity']
    .shift(1)
)

momentum_df['popularity_growth'] = (
    momentum_df['popularity']
    - momentum_df['previous_popularity']
)

momentum_df['momentum_score'] = (
    momentum_df['rank_jump'].fillna(0)
    +
    momentum_df['popularity_growth'].fillna(0)
)

top_momentum = (
    momentum_df.groupby(['song', 'artist'])['momentum_score']
    .mean()
    .reset_index()
)

fig6 = px.bar(
    top_momentum.sort_values(
        by='momentum_score',
        ascending=False
    ),
    x='song',
    y='momentum_score',
    color='artist',
    title='Momentum Score by Song'
)

st.plotly_chart(fig6, use_container_width=True)

# ---------------------------------------------------
# FANDOM INTENSITY SCORE
# ---------------------------------------------------

st.subheader("💜 Fandom Intensity Leaderboard")

fandom_df = (
    top_momentum.merge(
        reentry_df,
        on=['song', 'artist']
    )
)

fandom_df['fandom_score'] = (
    fandom_df['momentum_score']
    +
    fandom_df['reentry_count']
)

fandom_df = fandom_df.sort_values(
    by='fandom_score',
    ascending=False
)

st.dataframe(fandom_df)

# ---------------------------------------------------
# TOP FANDOM SONGS
# ---------------------------------------------------

fig7 = px.bar(
    fandom_df.head(10),
    x='song',
    y='fandom_score',
    color='artist',
    title='Top Fandom Intensity Songs'
)

st.plotly_chart(fig7, use_container_width=True)

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------

st.markdown("---")
st.markdown(
    "K-Pop Comeback Momentum & Fandom Analytics Dashboard"
)