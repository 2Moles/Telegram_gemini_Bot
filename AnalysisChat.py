import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from pymongo import MongoClient
nltk.download('vader_lexicon')

# Connect to MongoDB
client = MongoClient("mongodb+srv://mybtp:mybtp@node-api.cqbp1.mongodb.net/?retryWrites=true&w=majority&appName=Node-API")
db = client["Telegram"]
chat_history_collection = db["ChatHistory"]

# Initialize Sentiment Analyzer
sia = SentimentIntensityAnalyzer()

# Fetch Chat Data from MongoDB
chats = chat_history_collection.find()

# Analyze and Update Sentiment Scores
for chat in chats:
    text = chat["user_input"]  # Extract user message
    sentiment_score = sia.polarity_scores(text)["compound"]

    # Classify Sentiment
    if sentiment_score > 0.45:
        sentiment = "Positive"
    elif sentiment_score < -0.25:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    # Update MongoDB with sentimenti analysis
    chat_history_collection.update_one(
        {"_id": chat["_id"]},
        {"$set": {"sentiment": sentiment, "sentiment_score": sentiment_score}}
    )

print("✅ Sentiment analysis completed and updated in MongoDB!")
for chat in chat_history_collection.find({}, {"_id": 0, "user_input": 1, "sentiment": 1, "sentiment_score": 1}):
    print(chat)
