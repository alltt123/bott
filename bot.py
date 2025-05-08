import asyncio
import logging
import os
from collections import Counter
from datetime import datetime, timedelta

# Workaround for snscrape issue with Python 3.12+
import importlib.util
import snscrape.modules

if hasattr(importlib.util, 'find_spec'):
    for module_name in ['twitter']:
        spec = importlib.util.find_spec(f"snscrape.modules.{module_name}")
        if spec is not None:
            importlib.import_module(f"snscrape.modules.{module_name}")

import snscrape.modules.twitter as sntwitter
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

def analyze_hashtags_and_collect_links(target_hashtag, max_tweets=100, max_links=5):
    hashtag_counts = Counter()
    tweet_links = []

    now = datetime.utcnow()
    since_time = now - timedelta(hours=2)
    query = f'{target_hashtag} since:{since_time.date()} lang:en'

    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= max_tweets:
            break
        if tweet.date < since_time:
            continue

        hashtags = [word for word in tweet.content.split() if word.startswith("#")]
        for tag in hashtags:
            if tag.lower() != target_hashtag.lower():
                hashtag_counts[tag.lower()] += 1

        if len(tweet_links) < max_links:
            tweet_links.append(f"https://twitter.com/{tweet.user.username}/status/{tweet.id}")

    return hashtag_counts.most_common(10), tweet_links

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please specify a hashtag. Example: /analyze #AI")
        return

    hashtag = context.args[0]
    if not hashtag.startswith("#"):
        hashtag = "#" + hashtag

    await update.message.reply_text(f"🔍 Searching for tweets with {hashtag} in the last 2 hours...")

    top_hashtags, tweet_links = analyze_hashtags_and_collect_links(hashtag)

    if top_hashtags:
        response = f"📊 Top 10 hashtags co-occurring with {hashtag}:\n"
        for tag, count in top_hashtags:
            response += f"{tag}: {count} times\n"
    else:
        response = "❌ No related hashtags found."

    await update.message.reply_text(response)

    if tweet_links:
        links_response = "🥵 Here are some recent tweets:\n" + "\n".join(tweet_links)
        await update.message.reply_text(links_response)
    else:
        await update.message.reply_text("😕 No tweets found in the last 2 hours.")

def main():
    token = "AAEqZ02YI-SuWkv_X1ZXJTHtw5E51HcO51"
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("analyze", analyze))
    print("🤖 Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()

