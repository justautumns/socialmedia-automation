#!/usr/bin/env python3
"""very basic utility to scrape comments from an Instagram post and
record points to an Excel workbook.

usage:
    python insta-automation.py

The script asks for Instagram credentials, logs in, then asks for a post URL,
uses :pypi:`instaloader` to fetch comments and writes a row for every comment
(10 points each) into ``points.xlsx``. Existing data is preserved and new rows
are appended.
"""

import os
import re
import sys
import getpass

import instaloader
import pandas as pd


EXCEL_FILENAME = "points.xlsx"
POINTS_PER_COMMENT = 10


def extract_shortcode(post_url: str) -> str | None:
    """Extract the shortcode from an Instagram post URL.

    A normal post URL looks like ``https://www.instagram.com/p/ABC12345xyz/``.
    """

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
