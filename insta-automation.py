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
import getpass

import instaloader
import pandas as pd


EXCEL_FILENAME = "Social-points.xlsx"
POINTS_PER_COMMENT = 10  ## This will change due to Sylvia's rules, but for now it's a constant.


def extract_shortcode(post_url: str) -> str | None:
    # instagram post url should look like https://www.instagram.com/p/SHORTCODE/ or https://www.instagram.com/reel/SHORTCODE/

    match = re.search(r"/p/([^/]+)/", post_url)
    return match.group(1) if match else None



def main() -> None:
    loader = instaloader.Instaloader()

    username = input("Instagram username: ").strip()
    password = getpass.getpass("Instagram password: ").strip()

    try:
        loader.login(username, password)
        print("Login successful.")
    except Exception as exc:
        print("Login failed:", exc)
        sys.exit(1)

    url = input("Instagram post URL: ").strip()
    shortcode = extract_shortcode(url)
    if not shortcode:
        print("Could not parse a shortcode from that URL.")
        sys.exit(1)

    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
    except Exception as exc:  # network/permission etc.
        print("Failed to load post:", exc)
        sys.exit(1)

    print("Post caption:", (post.caption or "").replace("\n", " ")[:80])

    rows: list[tuple[str, int]] = []
    for comment in post.get_comments():
        rows.append((comment.owner.username, POINTS_PER_COMMENT))

    if not rows:
        print("No comments were fetched; exiting.")
        sys.exit(0)

    df_new = pd.DataFrame(rows, columns=["username", "points"])

    if os.path.exists(EXCEL_FILENAME):
        df_existing = pd.read_excel(EXCEL_FILENAME)
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_excel(EXCEL_FILENAME, index=False)
    print(f"Wrote {len(df_new)} comment(s) to {EXCEL_FILENAME}.")


if __name__ == "__main__":
    main()
