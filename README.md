# Instagram Post Tracker

A Streamlit-based application for tracking Instagram post interactions (likes and comments) and assigning social points to users. This tool helps automate the process of monitoring engagement on Instagram posts and maintaining a leaderboard of user contributions.

## Features

- **Instagram Login**: Secure login to Instagram accounts using Instaloader
- **Post Tracking**: Extract and analyze comments and likes from Instagram posts
- **Point System**: Assign points for comments (10 points each) and likes (10 points each) /Pretty usefull for rewarding system
- **Data Persistence**: Save user points to a CSV file and track processed posts to avoid duplicates
- **Real-time Updates**: Display top contributors in a sortable table
- **Download Functionality**: Export the full points data as a CSV file
- **Rate Limit Protection**: Built-in delays and retry mechanisms to avoid Instagram's rate limits

## Prerequisites

- Python 3.7+
- Instagram account (for login purposes)
- Internet connection

## Installation

1. Clone or download this repository:
   ```bash
   git clone <repository-url>
   cd Automationsforwork
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit application:
   ```bash
   streamlit run insta-automation.py
   ```

2. Open your browser to the provided local URL (usually `http://localhost:8501`)

3. Log in with your Instagram credentials

4. Enter an Instagram post URL in the format: `https://www.instagram.com/p/...` or `https://www.instagram.com/reel/...`

5. Click "Get the points!" to analyze the post

6. View the results in the table and download the CSV if needed

## Rate Limiting Precautions

To avoid being blocked by Instagram, please follow these guidelines:

- Do not run the program multiple times in a short period
- Check only one post URL at a time and close the browser tab before running again
- If the program fails, wait 5 minutes before retrying
- For multiple posts, wait 5 minutes between each analysis
- Do not exit the program between posts; instead, type `newpost` and press Enter

## Files

- `insta-automation.py`: Main application script
- `Social-points.csv`: Generated CSV file containing user points (created automatically)
- `tracked_posts.txt`: Text file tracking processed post URLs (created automatically)

## Disclaimer

This tool is for educational and personal use only. Be mindful of Instagram's Terms of Service and use responsibly. The developers are not responsible for any misuse or account restrictions that may occur.
