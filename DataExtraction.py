import os
import streamlit as st
import pandas as pd
import time
from pymongo import MongoClient
import nltk
from dotenv import load_dotenv

from nltk.sentiment import SentimentIntensityAnalyzer
load_dotenv(".env.local")

# Download NLTK Sentiment Lexicon
nltk.download("vader_lexicon")

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["Telegram"]
chat_history_collection = db["ChatHistory"]

# Initialize Sentiment Analyzer
sia = SentimentIntensityAnalyzer()

st.title("📊 Telegram Chat & Sentiment Analysis (Real-Time)")

# Function to Fetch Data
def fetch_data():
    """Fetch latest chat data from MongoDB and perform sentiment analysis."""
    chats = pd.DataFrame(list(chat_history_collection.find({}, {"_id": 0})))

    if chats.empty:
        return chats

    # Convert timestamp to datetime format
    if "timestamp" in chats.columns:
        chats["timestamp"] = pd.to_datetime(chats["timestamp"])

    # Perform Sentiment Analysis (if not already analyzed)
    for i, row in chats.iterrows():
        if "sentiment" not in row or "sentiment_score" not in row:
            sentiment_score = sia.polarity_scores(row["user_input"])["compound"]
            sentiment = "Positive" if sentiment_score > 0.05 else "Negative" if sentiment_score < -0.05 else "Neutral"

            # Update in MongoDB
            chat_history_collection.update_one(
                {"chat_id": row["chat_id"], "user_input": row["user_input"]},
                {"$set": {"sentiment": sentiment, "sentiment_score": sentiment_score}}
            )

            # Add to DataFrame
            chats.at[i, "sentiment"] = sentiment
            chats.at[i, "sentiment_score"] = sentiment_score

    return chats

# Live Data Update Loop
while True:
    df = fetch_data()

    if not df.empty:
        # Show latest messages
        st.subheader("💬 Latest Messages")
        st.dataframe(df.sort_values(by="timestamp", ascending=False).head(10))

        # Sentiment Distribution
        st.subheader("📊 Sentiment Distribution")
        sentiment_counts = df["sentiment"].value_counts()
        st.bar_chart(sentiment_counts)

        # Sentiment Score Trend
        st.subheader("📈 Sentiment Score Trend")
        if "timestamp" in df.columns and "sentiment_score" in df.columns:
            st.line_chart(df.set_index("timestamp")["sentiment_score"])

    time.sleep(5)  # Auto-update every 5 seconds
