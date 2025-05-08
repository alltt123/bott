import asyncio
import logging
import time
from collections import Counter
from datetime import datetime, timedelta

# Импортируем snscrape для поиска в Twitter
import snscrape.modules.twitter as sntwitter

# Настроим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_hashtags_and_collect_links(target_hashtag, max_tweets=50, max_links=5, retries=3, wait_time=5):
    hashtag_counts = Counter()
    tweet_links = []
    
    now = datetime.utcnow()
    since_time = now - timedelta(hours=2)
    query = f'{target_hashtag} since:{since_time.date()} lang:en'
    
    logger.info(f"Executing query: {query}")  # Логируем запрос

    attempt = 0
    while attempt < retries:
        try:
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

        except Exception as e:
            attempt += 1
            logger.error(f"Attempt {attempt} failed: {str(e)}")
            if attempt < retries:
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise

async def analyze(update, context):
    try:
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
    
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        await update.message.reply_text(f"An error occurred: {str(e)}")

def main():
    token = "7976774747:AAEqZ02YI-SuWkv_X1ZXJTHtw5E51HcO51g"
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("analyze", analyze))

    logger.info("Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()
