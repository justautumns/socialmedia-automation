#!/usr/bin/env python3

## Avoiding rate limit 
## 1.) Do not try to run the program multiple times in a short period of time.
## 2.) Check only url of the post and close the browser tab before running the program.
## 3.) If program fails unexpectedly, wait for 5 minutes before trying again.
## 4.) If you have multiple posts to check, wait 5 minutes between each post. Do not exit the program 
## just provide the new url by typing newpost and pressing Enter.
import os
import re
import sys
import time
import random
from collections import defaultdict

import instaloader
from instaloader import exceptions
import pandas as pd
import streamlit as st


CSV_FILENAME = "Social-points.csv"  # previously Excel, CSV avoids openpyxl dependency
POINTS_PER_COMMENT = 10  ## This will change due to Sylvia's rules, but for now it's a constant.
POINTS_PER_LIKE = 10  ## Points per like

TRACKED_URLS_FILENAME = "tracked_posts.txt"


def _tracked_urls_path() -> str:
    return os.path.join(os.path.dirname(__file__), TRACKED_URLS_FILENAME)


def load_tracked_urls() -> set[str]:
    path = _tracked_urls_path()
    if not os.path.exists(path):
        open(path, "w", encoding="utf-8").close()
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_tracked_url(url: str) -> None:
    path = _tracked_urls_path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(url.strip() + "\n")


def extract_shortcode(post_url: str) -> str | None:
    # instagram post url should look like https://www.instagram.com/p/SHORTCODE/ or https://www.instagram.com/reel/SHORTCODE/

    match = re.search(r"/p/([^/]+)/", post_url)
    return match.group(1) if match else None



def _get_post(loader: instaloader.Instaloader, shortcode: str, max_retries: int = 3) -> instaloader.Post:
    """Fetch a post and retry with backoff if Instagram throttles us."""
    attempt = 0
    while True:
        try:
            return instaloader.Post.from_shortcode(loader.context, shortcode)
        except exceptions.TooManyRequestsException as exc:
            attempt += 1
            wait = 300 * attempt
            st.write(f"Rate limit hit (429). sleeping {wait} seconds (attempt {attempt})...")
            if attempt >= max_retries:
                raise
            time.sleep(wait)
        except exceptions.ConnectionException as exc:
            # network issue, just bail out
            st.write("Network error while loading post:", exc)
            raise


st.title("Instagram Post Tracker")

st.write("Please follow the steps below")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.loader = None
    st.session_state.username = ""
    st.session_state.confirm_retrack = False
    st.session_state.pending_url = ""
    st.session_state.to_track_url = ""
    st.session_state.do_track = False

if st.session_state.logged_in:
    st.success(f"Logged in as {st.session_state.username}")
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.loader = None
        st.session_state.username = ""
        st.session_state.confirm_retrack = False
        st.session_state.pending_url = ""
        st.experimental_rerun()
else:
    with st.form("login_form"):
        st.session_state.username = st.text_input("Instagram username:", value=st.session_state.username)
        password = st.text_input("Instagram password:", type="password")
        if st.form_submit_button("Login"):
            loader = instaloader.Instaloader()
            try:
                loader.login(st.session_state.username, password)
                st.session_state.logged_in = True
                st.session_state.loader = loader
                st.success("Login successful.")
            except Exception as exc:
                st.error(f"Login failed: {exc}")

tracked_urls = load_tracked_urls()

post_url = st.text_input("Enter the post URL:", value=st.session_state.pending_url)

if st.button("Track Post"):
    if not post_url:
        st.error("Please enter a valid Instagram post URL.")
    else:
        st.session_state.to_track_url = post_url
        st.session_state.do_track = True
        st.session_state.pending_url = post_url
        if not st.session_state.logged_in:
            st.warning("Please log in first to track this post.")

# If we are supposed to track and user is logged in, do it now.
if st.session_state.do_track and st.session_state.logged_in:
    st.session_state.do_track = False
    st.session_state.pending_url = ""

    post_url = st.session_state.to_track_url
    if not post_url:
        st.error("No post URL was provided.")
    else:
        if post_url in tracked_urls and not st.session_state.confirm_retrack:
            st.warning("This post has already been tracked. Do you want to track it again?")
            if st.button("Yes, track again", key="confirm_yes"):
                st.session_state.confirm_retrack = True
                st.session_state.to_track_url = post_url
                st.session_state.do_track = True
                st.experimental_rerun()
            if st.button("No, pick another post", key="confirm_no"):
                st.session_state.confirm_retrack = False
                st.session_state.to_track_url = ""
                st.experimental_rerun()
        else:
            st.session_state.confirm_retrack = False

            st.write("Tracking post performance...")
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.05)
                progress_bar.progress(i + 1)

            if st.session_state.loader is None:
                st.error("Session expired or loader not found. Please log in again.")
                st.stop()

            loader = st.session_state.loader

            shortcode = extract_shortcode(post_url)
            if not shortcode:
                st.error("Could not parse a shortcode from that URL.")
                st.stop()

            try:
                post = _get_post(loader, shortcode)
            except Exception as exc:
                st.error(f"Failed to load post: {exc}")
                st.stop()

            st.write("Post caption:", (post.caption or "").replace("\n", " ")[:80])

            user_data = defaultdict(lambda: {'points': 0, 'comments': 0, 'likes': 0})
            for comment in post.get_comments():
                user = comment.owner.username
                user_data[user]['points'] += POINTS_PER_COMMENT
                user_data[user]['comments'] += 1
                time.sleep(random.uniform(0.5, 1.5))

            try:
                for like in post.get_likes():
                    user = like.username
                    user_data[user]['points'] += POINTS_PER_LIKE
                    user_data[user]['likes'] += 1
                    time.sleep(random.uniform(0.5, 1.5))
            except exceptions.ConnectionException:
                st.write("Could not fetch likes for this post (Instagram may not allow it for this content). Proceeding with comments only.")
            except Exception as exc:
                st.write(f"Error fetching likes: {exc}. Proceeding with comments only.")

            if not user_data:
                st.write("No interactions were fetched for this post.")
                df = pd.DataFrame(columns=['Username', 'Points', 'Comments', 'Likes'])
            else:
                if os.path.exists(CSV_FILENAME):
                    df_existing = pd.read_csv(CSV_FILENAME)
                    existing_points = dict(zip(df_existing['username'], df_existing['points']))
                else:
                    existing_points = {}

                for user, data in user_data.items():
                    if user in existing_points:
                        existing_points[user] += data['points']
                    else:
                        existing_points[user] = data['points']

                df_all = pd.DataFrame(list(existing_points.items()), columns=['username', 'points'])
                df_all.to_csv(CSV_FILENAME, index=False)
                st.write(f"Updated {len(user_data)} user(s) in {CSV_FILENAME}.")

                df = pd.DataFrame([{'Username': u, 'Points': d['points'], 'Comments': d['comments'], 'Likes': d['likes']} for u, d in user_data.items()])

            st.write("Post performance over time:")
            st.success("Tracking complete!")
            st.table(df)

            csv_path = os.path.join(os.path.dirname(__file__), CSV_FILENAME)
            df_all.to_csv(csv_path, index=False)

            with open(csv_path, "rb") as f:
                csv_data = f.read()

            st.download_button(
                label="Download data as CSV",
                data=csv_data,
                file_name=CSV_FILENAME,
                mime='text/csv',
            )

            if post_url not in tracked_urls:
                save_tracked_url(post_url)
else:
    st.info("Log in first to track posts.")
