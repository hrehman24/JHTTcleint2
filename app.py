import altair as alt
import os
import pandas as pd
import requests
import streamlit as st

from api_client import BeatifyClient


st.set_page_config(page_title="Beatify Client", page_icon="music", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --bg: #f4f6f8;
        --panel: #ffffff;
        --primary: #0f766e;
        --accent: #f59e0b;
        --muted: #6b7280;
    }

    .stApp {
        background: radial-gradient(circle at top right, #fff8ec 0%, var(--bg) 45%);
    }

    .hero {
        border-radius: 16px;
        background: linear-gradient(120deg, #0f766e 0%, #115e59 45%, #f59e0b 120%);
        color: white;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px rgba(15, 118, 110, 0.2);
    }

    .hero h1 {
        font-size: 1.6rem;
        margin: 0;
    }

    .hero p {
        margin: 0.35rem 0 0 0;
        opacity: 0.95;
    }

    [data-testid="stSidebar"] .stButton > button {
        border-radius: 999px;
        border: 1px solid #0f766e;
        background: #ecfeff;
        color: #0f766e;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        border-color: #115e59;
        background: #ccfbf1;
        color: #115e59;
        transform: translateY(-1px);
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        border-color: #f59e0b;
        background: linear-gradient(120deg, #f59e0b 0%, #d97706 100%);
        color: white;
        box-shadow: 0 6px 14px rgba(245, 158, 11, 0.35);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def extract_error(response):
    if response is None:
        return "No response"
    try:
        payload = response.json()
        if isinstance(payload, dict) and payload.get("message"):
            return str(payload.get("message"))
    except ValueError:
        pass
    text = (response.text or "").strip()
    return text or "Unknown error"


def action_feedback(response, success_message):
    if response.status_code in (200, 201):
        st.success(success_message)
        st.rerun()
    else:
        st.error(f"Error {response.status_code}: {extract_error(response)}")


def safe_list(fetcher, label):
    try:
        payload = fetcher()
    except requests.RequestException as exc:
        st.error(f"Unable to load {label}: {exc}")
        return []

    if isinstance(payload, list):
        return payload
    return []


def safe_response(fetcher, *args):
    try:
        response = fetcher(*args)
        return response, None
    except requests.RequestException as exc:
        return None, str(exc)


def options_with_ids(items, name_key="name"):
    mapping = {}
    for item in items:
        item_id = item.get("id")
        if item_id is None:
            continue
        label = f"{item.get(name_key, 'Unknown')} (ID: {item_id})"
        mapping[label] = item_id
    return mapping


def display_table(rows, columns, empty_text):
    if not rows:
        st.info(empty_text)
        return
    table_rows = [{column: row.get(column) for column in columns} for row in rows]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)


def show_dashboard(client):
    st.subheader("Overview")

    root_resp, root_err = safe_response(client.get_aux_root)
    if root_err:
        st.warning(f"Aux service is not reachable: {root_err}")
    elif root_resp and root_resp.status_code in (200, 201):
        st.success("Auxiliary service connected")
    else:
        code = root_resp.status_code if root_resp else "N/A"
        st.warning(f"Auxiliary service returned HTTP {code}")

    summary_resp, summary_err = safe_response(client.get_analytics_summary)
    if summary_err:
        st.error(f"Could not load summary analytics: {summary_err}")
        return

    if not summary_resp or summary_resp.status_code != 200:
        code = summary_resp.status_code if summary_resp else "N/A"
        err = extract_error(summary_resp)
        st.error(f"Summary endpoint failed with HTTP {code}: {err}")
        return

    summary = summary_resp.json()
    counts = summary.get("counts", {})
    metrics = summary.get("metrics", {})

    st.caption("Dashboard combines core API entities with auxiliary analytics for quick monitoring.")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Artists", counts.get("artists", 0))
    c2.metric("Albums", counts.get("albums", 0))
    c3.metric("Tracks", counts.get("tracks", 0))
    c4.metric("Users", counts.get("users", 0))
    c5.metric("Playlists", counts.get("playlists", 0))

    m1, m2 = st.columns(2)
    m1.metric("Avg Track Length (sec)", metrics.get("average_track_length_seconds", 0))
    m2.metric("Tracks / Album", metrics.get("tracks_per_album_ratio", 0))

    st.markdown("### Snapshot")

    counts_df = pd.DataFrame(
        [
            {"entity": "Artists", "count": counts.get("artists", 0)},
            {"entity": "Albums", "count": counts.get("albums", 0)},
            {"entity": "Tracks", "count": counts.get("tracks", 0)},
            {"entity": "Users", "count": counts.get("users", 0)},
            {"entity": "Playlists", "count": counts.get("playlists", 0)},
        ]
    )

    donut = (
        alt.Chart(counts_df)
        .mark_arc(innerRadius=55, outerRadius=95)
        .encode(
            theta=alt.Theta("count:Q", title="Count"),
            color=alt.Color(
                "entity:N",
                scale=alt.Scale(range=["#0f766e", "#14b8a6", "#f59e0b", "#475569", "#22c55e"]),
                legend=alt.Legend(title="Entity"),
            ),
            tooltip=["entity:N", "count:Q"],
        )
        .properties(height=260)
    )

    top_resp, top_err = safe_response(client.get_top_artists)

    left, right = st.columns([1.1, 1.4])
    with left:
        st.markdown("#### Data Composition")
        st.altair_chart(donut, use_container_width=True)

    with right:
        st.markdown("#### Top Artists by Track Count")
        if top_err:
            st.error(f"Could not load top artists: {top_err}")
        elif not top_resp or top_resp.status_code != 200:
            code = top_resp.status_code if top_resp else "N/A"
            err = extract_error(top_resp)
            st.error(f"Top artists endpoint failed with HTTP {code}: {err}")
        else:
            items = top_resp.json().get("items", [])
            if items:
                top_df = pd.DataFrame(items)
                top_chart = (
                    alt.Chart(top_df)
                    .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
                    .encode(
                        x=alt.X("track_count:Q", title="Track Count"),
                        y=alt.Y("artist_name:N", title="Artist", sort="-x"),
                        color=alt.value("#0f766e"),
                        tooltip=["artist_name:N", "track_count:Q"],
                    )
                    .properties(height=260)
                )
                st.altair_chart(top_chart, use_container_width=True)
            else:
                st.info("No top artist data available yet.")

    st.markdown("### Track Insights")
    tracks = safe_list(client.get_tracks, "tracks")
    albums = safe_list(client.get_albums, "albums")

    if not tracks:
        st.info("No tracks available for insight charts.")
        return

    tracks_df = pd.DataFrame(tracks)
    if "length" in tracks_df.columns:
        lengths_df = tracks_df[pd.to_numeric(tracks_df["length"], errors="coerce").notna()].copy()
        if not lengths_df.empty:
            lengths_df["length"] = lengths_df["length"].astype(int)

            hist = (
                alt.Chart(lengths_df)
                .mark_bar(color="#f59e0b", opacity=0.8)
                .encode(
                    x=alt.X("length:Q", bin=alt.Bin(maxbins=25), title="Track Length (sec)"),
                    y=alt.Y("count():Q", title="Number of Tracks"),
                    tooltip=[alt.Tooltip("count():Q", title="Tracks")],
                )
                .properties(height=260)
            )

            trend_source = lengths_df.sort_values(by="length").reset_index(drop=True)
            trend_source["rank"] = trend_source.index + 1
            trend = (
                alt.Chart(trend_source)
                .mark_line(color="#0f766e", strokeWidth=3)
                .encode(
                    x=alt.X("rank:Q", title="Track Position (sorted by length)"),
                    y=alt.Y("length:Q", title="Length (sec)"),
                    tooltip=["rank:Q", "length:Q"],
                )
                .properties(height=260)
            )

            l_col, r_col = st.columns(2)
            with l_col:
                st.markdown("#### Length Distribution")
                st.altair_chart(hist, use_container_width=True)
            with r_col:
                st.markdown("#### Length Trend")
                st.altair_chart(trend, use_container_width=True)

    if albums and "album_id" in tracks_df.columns:
        albums_df = pd.DataFrame(albums)
        if {"id", "name"}.issubset(set(albums_df.columns)):
            album_counts_df = (
                tracks_df.groupby("album_id", dropna=True)
                .size()
                .reset_index(name="track_count")
                .merge(albums_df[["id", "name"]], left_on="album_id", right_on="id", how="left")
            )
            album_counts_df["name"] = album_counts_df["name"].fillna("Unknown")
            album_counts_df = album_counts_df.sort_values(by="track_count", ascending=False).head(10)

            if not album_counts_df.empty:
                album_chart = (
                    alt.Chart(album_counts_df)
                    .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
                    .encode(
                        x=alt.X("track_count:Q", title="Track Count"),
                        y=alt.Y("name:N", sort="-x", title="Album"),
                        color=alt.value("#14b8a6"),
                        tooltip=["name:N", "track_count:Q"],
                    )
                    .properties(height=320)
                )
                st.markdown("#### Top Albums by Number of Tracks")
                st.altair_chart(album_chart, use_container_width=True)


def show_aux_service(client):
    st.subheader("Auxiliary Service")

    overview_tab, analytics_tab, top_tab, recommendations_tab = st.tabs(
        ["Overview", "Analytics Summary", "Top Artists", "Recommendations"]
    )

    with overview_tab:
        root_resp, root_err = safe_response(client.get_aux_root)
        if root_err:
            st.error(f"Aux service is not reachable: {root_err}")
        elif not root_resp or root_resp.status_code != 200:
            code = root_resp.status_code if root_resp else "N/A"
            err = extract_error(root_resp)
            st.error(f"Aux service check failed with HTTP {code}: {err}")
        else:
            st.success("Auxiliary service connected")
            st.json(root_resp.json())

    with analytics_tab:
        summary_resp, summary_err = safe_response(client.get_analytics_summary)
        if summary_err:
            st.error(f"Could not load summary analytics: {summary_err}")
        elif not summary_resp or summary_resp.status_code != 200:
            code = summary_resp.status_code if summary_resp else "N/A"
            err = extract_error(summary_resp)
            st.error(f"Summary endpoint failed with HTTP {code}: {err}")
        else:
            st.json(summary_resp.json())

    with top_tab:
        top_resp, top_err = safe_response(client.get_top_artists)
        if top_err:
            st.error(f"Could not load top artists: {top_err}")
        elif not top_resp or top_resp.status_code != 200:
            code = top_resp.status_code if top_resp else "N/A"
            err = extract_error(top_resp)
            st.error(f"Top artists endpoint failed with HTTP {code}: {err}")
        else:
            st.json(top_resp.json())

    with recommendations_tab:
        show_recommendations(client)


def show_artists(client):
    artists = safe_list(client.get_artists, "artists")

    left, right = st.columns([1.4, 1])
    with left:
        st.subheader("Artists")
        display_table(artists, ["id", "name"], "No artists found.")

    with right:
        st.subheader("Manage")
        create_tab, update_tab, delete_tab = st.tabs(["Create", "Update", "Delete"])

        with create_tab:
            name = st.text_input("Artist name", key="artist_create_name")
            if st.button("Create Artist", key="artist_create_btn"):
                if not name.strip():
                    st.warning("Please enter a name.")
                else:
                    response = client.create_artist(name.strip())
                    action_feedback(response, f"Artist '{name.strip()}' created.")

        with update_tab:
            options = options_with_ids(artists)
            if not options:
                st.info("Create at least one artist to update.")
            else:
                selected = st.selectbox("Select artist", list(options.keys()), key="artist_update_select")
                new_name = st.text_input("New artist name", key="artist_update_name")
                if st.button("Update Artist", key="artist_update_btn"):
                    if not new_name.strip():
                        st.warning("Please enter a new name.")
                    else:
                        response = client.update_artist(options[selected], new_name.strip())
                        action_feedback(response, "Artist updated.")

        with delete_tab:
            options = options_with_ids(artists)
            if not options:
                st.info("Create at least one artist to delete.")
            else:
                selected = st.selectbox("Select artist", list(options.keys()), key="artist_delete_select")
                if st.button("Delete Artist", key="artist_delete_btn"):
                    response = client.delete_artist(options[selected])
                    action_feedback(response, "Artist deleted.")


def show_albums(client):
    artists = safe_list(client.get_artists, "artists")
    albums = safe_list(client.get_albums, "albums")

    artist_lookup = {a.get("id"): a.get("name", "Unknown") for a in artists}
    album_rows = [
        {
            "id": album.get("id"),
            "name": album.get("name"),
            "artist": artist_lookup.get(album.get("artist_id"), "Unknown"),
        }
        for album in albums
    ]

    left, right = st.columns([1.4, 1])
    with left:
        st.subheader("Albums")
        display_table(album_rows, ["id", "name", "artist"], "No albums found.")

    with right:
        st.subheader("Manage")
        create_tab, update_tab, delete_tab = st.tabs(["Create", "Update", "Delete"])

        artist_options = options_with_ids(artists)
        album_options = options_with_ids(albums)

        with create_tab:
            name = st.text_input("Album name", key="album_create_name")
            if artist_options:
                selected_artist = st.selectbox("Artist", list(artist_options.keys()), key="album_create_artist")
                if st.button("Create Album", key="album_create_btn"):
                    if not name.strip():
                        st.warning("Please enter an album name.")
                    else:
                        response = client.create_album(name.strip(), artist_options[selected_artist])
                        action_feedback(response, f"Album '{name.strip()}' created.")
            else:
                st.info("Create an artist first.")

        with update_tab:
            if not album_options or not artist_options:
                st.info("You need both artists and albums to update an album.")
            else:
                selected_album = st.selectbox("Album", list(album_options.keys()), key="album_update_select")
                selected_artist = st.selectbox("New artist", list(artist_options.keys()), key="album_update_artist")
                new_name = st.text_input("New album name", key="album_update_name")
                if st.button("Update Album", key="album_update_btn"):
                    if not new_name.strip():
                        st.warning("Please enter a new album name.")
                    else:
                        response = client.update_album(
                            album_options[selected_album],
                            new_name.strip(),
                            artist_options[selected_artist],
                        )
                        action_feedback(response, "Album updated.")

        with delete_tab:
            if not album_options:
                st.info("Create at least one album to delete.")
            else:
                selected_album = st.selectbox("Album", list(album_options.keys()), key="album_delete_select")
                if st.button("Delete Album", key="album_delete_btn"):
                    response = client.delete_album(album_options[selected_album])
                    action_feedback(response, "Album deleted.")


def show_tracks(client):
    albums = safe_list(client.get_albums, "albums")
    tracks = safe_list(client.get_tracks, "tracks")

    album_lookup = {a.get("id"): a.get("name", "Unknown") for a in albums}
    track_rows = [
        {
            "id": track.get("id"),
            "name": track.get("name"),
            "length": track.get("length"),
            "album": album_lookup.get(track.get("album_id"), "Unknown"),
        }
        for track in tracks
    ]

    left, right = st.columns([1.4, 1])
    with left:
        st.subheader("Tracks")
        display_table(track_rows, ["id", "name", "length", "album"], "No tracks found.")

    with right:
        st.subheader("Manage")
        create_tab, update_tab, delete_tab = st.tabs(["Create", "Update", "Delete"])

        album_options = options_with_ids(albums)
        track_options = options_with_ids(tracks)

        with create_tab:
            name = st.text_input("Track name", key="track_create_name")
            length = st.number_input("Length (seconds)", min_value=1, step=1, key="track_create_length")
            if album_options:
                selected_album = st.selectbox("Album", list(album_options.keys()), key="track_create_album")
                if st.button("Create Track", key="track_create_btn"):
                    if not name.strip():
                        st.warning("Please enter a track name.")
                    else:
                        response = client.create_track(name.strip(), int(length), album_options[selected_album])
                        action_feedback(response, f"Track '{name.strip()}' created.")
            else:
                st.info("Create an album first.")

        with update_tab:
            if not track_options or not album_options:
                st.info("You need both albums and tracks to update a track.")
            else:
                selected_track = st.selectbox("Track", list(track_options.keys()), key="track_update_select")
                selected_album = st.selectbox("Album", list(album_options.keys()), key="track_update_album")
                new_name = st.text_input("New track name", key="track_update_name")
                new_length = st.number_input("New length (seconds)", min_value=1, step=1, key="track_update_length")
                if st.button("Update Track", key="track_update_btn"):
                    if not new_name.strip():
                        st.warning("Please enter a new track name.")
                    else:
                        response = client.update_track(
                            track_options[selected_track],
                            new_name.strip(),
                            int(new_length),
                            album_options[selected_album],
                        )
                        action_feedback(response, "Track updated.")

        with delete_tab:
            if not track_options:
                st.info("Create at least one track to delete.")
            else:
                selected_track = st.selectbox("Track", list(track_options.keys()), key="track_delete_select")
                if st.button("Delete Track", key="track_delete_btn"):
                    response = client.delete_track(track_options[selected_track])
                    action_feedback(response, "Track deleted.")


def show_users(client):
    users = safe_list(client.get_users, "users")

    left, right = st.columns([1.4, 1])
    with left:
        st.subheader("Users")
        display_table(users, ["id", "name"], "No users found.")

    with right:
        st.subheader("Manage")
        create_tab, update_tab, delete_tab = st.tabs(["Create", "Update", "Delete"])

        with create_tab:
            name = st.text_input("User name", key="user_create_name")
            if st.button("Create User", key="user_create_btn"):
                if not name.strip():
                    st.warning("Please enter a user name.")
                else:
                    response = client.create_user(name.strip())
                    action_feedback(response, f"User '{name.strip()}' created.")

        with update_tab:
            user_options = options_with_ids(users)
            if not user_options:
                st.info("Create at least one user to update.")
            else:
                selected = st.selectbox("User", list(user_options.keys()), key="user_update_select")
                new_name = st.text_input("New user name", key="user_update_name")
                if st.button("Update User", key="user_update_btn"):
                    if not new_name.strip():
                        st.warning("Please enter a new name.")
                    else:
                        response = client.update_user(user_options[selected], new_name.strip())
                        action_feedback(response, "User updated.")

        with delete_tab:
            user_options = options_with_ids(users)
            if not user_options:
                st.info("Create at least one user to delete.")
            else:
                selected = st.selectbox("User", list(user_options.keys()), key="user_delete_select")
                if st.button("Delete User", key="user_delete_btn"):
                    response = client.delete_user(user_options[selected])
                    action_feedback(response, "User deleted.")


def show_playlists(client):
    playlists = safe_list(client.get_playlists, "playlists")
    tracks = safe_list(client.get_tracks, "tracks")
    users = safe_list(client.get_users, "users")

    left, right = st.columns([1.4, 1])
    with left:
        st.subheader("Playlists")
        display_table(playlists, ["id", "name", "description"], "No playlists found.")

    with right:
        st.subheader("Manage")
        create_tab, update_tab, delete_tab, add_track_tab, add_user_tab = st.tabs(
            ["Create", "Update", "Delete", "Add Track", "Add User"]
        )

        playlist_options = options_with_ids(playlists)
        track_options = options_with_ids(tracks)
        user_options = options_with_ids(users)

        with create_tab:
            name = st.text_input("Playlist name", key="playlist_create_name")
            description = st.text_input("Description", key="playlist_create_desc")
            if st.button("Create Playlist", key="playlist_create_btn"):
                if not name.strip():
                    st.warning("Please enter a playlist name.")
                else:
                    response = client.create_playlist(name.strip(), description.strip() or "No description")
                    action_feedback(response, f"Playlist '{name.strip()}' created.")

        with update_tab:
            if not playlist_options:
                st.info("Create at least one playlist to update.")
            else:
                selected = st.selectbox("Playlist", list(playlist_options.keys()), key="playlist_update_select")
                new_name = st.text_input("New playlist name", key="playlist_update_name")
                new_desc = st.text_input("New description", key="playlist_update_desc")
                if st.button("Update Playlist", key="playlist_update_btn"):
                    if not new_name.strip():
                        st.warning("Please enter a new name.")
                    else:
                        response = client.update_playlist(playlist_options[selected], new_name.strip(), new_desc.strip())
                        action_feedback(response, "Playlist updated.")

        with delete_tab:
            if not playlist_options:
                st.info("Create at least one playlist to delete.")
            else:
                selected = st.selectbox("Playlist", list(playlist_options.keys()), key="playlist_delete_select")
                if st.button("Delete Playlist", key="playlist_delete_btn"):
                    response = client.delete_playlist(playlist_options[selected])
                    action_feedback(response, "Playlist deleted.")

        with add_track_tab:
            if not playlist_options or not track_options:
                st.info("You need both playlists and tracks for this action.")
            else:
                selected_playlist = st.selectbox("Playlist", list(playlist_options.keys()), key="playlist_add_track_p")
                selected_track = st.selectbox("Track", list(track_options.keys()), key="playlist_add_track_t")
                if st.button("Add Track To Playlist", key="playlist_add_track_btn"):
                    response = client.add_track_to_playlist(
                        playlist_options[selected_playlist],
                        track_options[selected_track],
                    )
                    action_feedback(response, "Track added to playlist.")

        with add_user_tab:
            if not playlist_options or not user_options:
                st.info("You need both playlists and users for this action.")
            else:
                selected_playlist = st.selectbox("Playlist", list(playlist_options.keys()), key="playlist_add_user_p")
                selected_user = st.selectbox("User", list(user_options.keys()), key="playlist_add_user_u")
                if st.button("Add User To Playlist", key="playlist_add_user_btn"):
                    response = client.add_user_to_playlist(
                        playlist_options[selected_playlist],
                        user_options[selected_user],
                    )
                    action_feedback(response, "User added to playlist.")


def show_recommendations(client):
    st.subheader("User Recommendations")
    users = safe_list(client.get_users, "users")
    user_options = options_with_ids(users)

    if not user_options:
        st.info("No users available. Create users first.")
        return

    selected_user = st.selectbox("Choose user", list(user_options.keys()), key="recommend_user")
    if st.button("Get Recommendations", key="recommend_btn"):
        response, err = safe_response(client.get_user_recommendations, user_options[selected_user])
        if err:
            st.error(f"Recommendation request failed: {err}")
            return

        if response and response.status_code == 200:
            payload = response.json()
            st.caption(payload.get("algorithm", ""))
            items = payload.get("items", [])
            if items:
                st.dataframe(items, use_container_width=True, hide_index=True)
            else:
                st.info("No recommendation candidates found.")
        else:
            code = response.status_code if response else "N/A"
            msg = extract_error(response)
            st.error(f"Could not load recommendations (HTTP {code}): {msg}")


if "base_url" not in st.session_state:
    st.session_state["base_url"] = os.getenv("CORE_API_URL", "http://130.162.240.153:5000")
if "aux_url" not in st.session_state:
    st.session_state["aux_url"] = os.getenv("AUX_API_URL", "http://localhost:7000")

st.sidebar.title("Beatify API Client")
st.sidebar.caption("Core + Auxiliary Service")

st.sidebar.text_input("Core API URL", key="base_url")
st.sidebar.text_input("Auxiliary Service URL", key="aux_url")

if "service_tab" not in st.session_state:
    st.session_state["service_tab"] = "Main"

st.sidebar.markdown("### Service Tabs")
b1, b2, b3 = st.sidebar.columns(3)
with b1:
    if st.button(
        "Main",
        key="service_btn_main",
        type="primary" if st.session_state["service_tab"] == "Main" else "secondary",
        use_container_width=True,
    ):
        st.session_state["service_tab"] = "Main"
with b2:
    if st.button(
        "Core",
        key="service_btn_core",
        type="primary" if st.session_state["service_tab"] == "Core Service" else "secondary",
        use_container_width=True,
    ):
        st.session_state["service_tab"] = "Core Service"
with b3:
    if st.button(
        "Aux",
        key="service_btn_aux",
        type="primary" if st.session_state["service_tab"] == "Aux Service" else "secondary",
        use_container_width=True,
    ):
        st.session_state["service_tab"] = "Aux Service"

service_tab = st.session_state["service_tab"]
if service_tab == "Main":
    page = "Dashboard"
elif service_tab == "Core Service":
    page = st.sidebar.radio("Core Options", ["Artists", "Albums", "Tracks", "Users", "Playlists"])
else:
    page = "Aux Service"

client = BeatifyClient(
    base_url=st.session_state["base_url"],
    aux_url=st.session_state["aux_url"],
)

st.markdown(
    """
    <div class="hero">
      <h1>Beatify Control Center</h1>
      <p>Manage your music data and view analytics from the auxiliary service.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if page == "Dashboard":
    show_dashboard(client)
elif page == "Artists":
    show_artists(client)
elif page == "Albums":
    show_albums(client)
elif page == "Tracks":
    show_tracks(client)
elif page == "Users":
    show_users(client)
elif page == "Playlists":
    show_playlists(client)
elif page == "Aux Service":
    show_aux_service(client)
