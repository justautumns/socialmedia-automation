#!/usr/bin/env python3

## Avoiding rate limit 
## 1.) Do not try to run the program multiple times in a short period of time.
## 2.) Check only url of the post and close the browser tab before running the program.
## 3.) If program fails unexpectedly, wait for 5 minutes before trying again.
## 4.) If you have multiple posts to check, wait 5 minutes between each post. Do not exit the program 
## just provide the new url by typing newpost and pressing Enter.
import os
import re
import time
import random
import instaloader
import pandas as pd
import streamlit as st
from collections import defaultdict
from instaloader import exceptions

CSV_FILENAME = "Social-points.csv"
TRACKED_URLS_FILENAME = "tracked_posts.txt"
POINTS_PER_COMMENT = 10
POINTS_PER_LIKE = 10

def _tracked_urls_path(): # We need to check the post was already tracked or not, to avoid duplicates. So we keep a list of tracked urls in a text file.
    return os.path.join(os.path.dirname(__file__), TRACKED_URLS_FILENAME)

def load_tracked_urls():
    path = _tracked_urls_path()
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_tracked_url(url):
    path = _tracked_urls_path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(url.strip() + "\n")

def extract_shortcode(post_url):
    # checking the shortcode
    match = re.search(r"/(p|reel|tv)/([^/?#&]+)", post_url)
    return match.group(2) if match else None

def _get_post(loader, shortcode, max_retries=3):
    attempt = 0
    while True:
        try:
            return instaloader.Post.from_shortcode(loader.context, shortcode)
        except exceptions.TooManyRequestsException:
            attempt += 1
            wait = 300 * attempt # Rate limit protection
            st.warning(f"Instagram rate limiterror (429). {wait} waiting for the next {attempt})")
            if attempt >= max_retries: raise
            time.sleep(wait)

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.loader = None
    st.session_state.username = ""

# --- 3. GUI PART---
st.set_page_config(page_title="InstaTracker", page_icon="📸")
st.title("📸 Instagram Post Tracker")

if not st.session_state.logged_in:
    st.info("Please log in with your Instagram account to continue.")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if u and p:
                loader = instaloader.Instaloader()
                try:
                    loader.login(u, p)
                    st.session_state.logged_in = True
                    st.session_state.loader = loader
                    st.session_state.username = u
                    st.success("Login successful! Preparing...")
                    time.sleep(1)
                    st.rerun() # Clear the form and move to the main app
                except Exception as e:
                    st.error(f"Login error: {e}")
            else:
                st.warning("Please enter a username and password.")
    st.stop() # Display only the login form until logged in

# --- GUI PART ---
st.sidebar.success(f"Login Successful: {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.loader = None
    st.rerun()

tracked_urls = load_tracked_urls()
post_url = st.text_input("Instagram Post URL:", placeholder="https://www.instagram.com/p/...")

if st.button("Get the points!"):
    if not post_url:
        st.error("Please enter a URL.")
    else:
        shortcode = extract_shortcode(post_url)
        if not shortcode:
            st.error("Invalid URL. Please check the format.")
        else:
            if post_url in tracked_urls:
                st.warning("This post has been tracked before. New points will be added to existing ones.")

            with st.status("Data collection started...", expanded=True) as status:
                try:
                    loader = st.session_state.loader
                    post = _get_post(loader, shortcode)
                    
                    user_data = defaultdict(lambda: {'points': 0, 'comments': 0, 'likes': 0})
                    
                    # --- COMMENTS ---
                    st.write("🗨️ Checking for comments...")
                    comment_count = 0
                    for comment in post.get_comments():
                        user = comment.owner.username
                        user_data[user]['points'] += POINTS_PER_COMMENT
                        user_data[user]['comments'] += 1
                        comment_count += 1
                        # sleep to avoid rate limits
                        time.sleep(random.uniform(0.3, 0.7))
                    
                    # --- LIKES (NOT GONNA WORK) ---
                    st.write("❤️ Checking for likes...")
                    like_count = 0
                    try:
                        for like in post.get_likes():
                            user = like.username
                            user_data[user]['points'] += POINTS_PER_LIKE
                            user_data[user]['likes'] += 1
                            like_count += 1
                            
                            # sleep to avoid rate limits
                            if like_count % 50 == 0:
                                st.write(f"next likes collected (Total: {like_count})")
                                time.sleep(random.uniform(5, 8))
                            else:
                                time.sleep(random.uniform(0.6, 1.2))
                    except Exception as le:
                        st.warning("Like list is restricted by Instagram. Only collected ones will be saved.")

                    # --- Data collection ---
                    if user_data:
                        # Table
                        df_display = pd.DataFrame([
                            {'Username': u, 'Points': d['points'], 'Comments': d['comments'], 'Likes': d['likes']} 
                            for u, d in user_data.items()
                        ]).sort_values(by='Points', ascending=False)
                        
                        # Update CSV
                        if os.path.exists(CSV_FILENAME):
                            df_main = pd.read_csv(CSV_FILENAME)
                        else:
                            df_main = pd.DataFrame(columns=['username', 'points'])

                        for u, d in user_data.items():
                            if u in df_main['username'].values:
                                df_main.loc[df_main['username'] == u, 'points'] += d['points']
                            else:
                                new_row = pd.DataFrame({'username': [u], 'points': [d['points']]})
                                df_main = pd.concat([df_main, new_row], ignore_index=True)

                        df_main.to_csv(CSV_FILENAME, index=False)
                        save_tracked_url(post_url)
                        
                        status.update(label="Completed succesfully!", state="complete", expanded=False)
                        st.success(f"Totaly {len(user_data)} users found with {comment_count} comments and {like_count} likes.")
                        st.table(df_display.head(20)) # First 20 users with the most points
                        
                        # Download Button
                        with open(CSV_FILENAME, "rb") as f:
                            st.download_button("Download Entire List (CSV)", f, file_name=CSV_FILENAME)
                    else:
                        st.info("No interactions found on this post.")
                
                except Exception as e:
                    st.error(f"Unexpected error occurred: {e}")