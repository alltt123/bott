import asyncio
import logging
import time
import ssl
from collections import Counter
from datetime import datetime, timedelta

import snscrape.modules.twitter as sntwitter
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /analyze #hashtag, чтобы проанализировать хэштег в Twitter.")


def analyze_hashtags_and_collect_links(target_hashtag, max_tweets=50, max_links=5, retries=3, wait_time=5):
    hashtag_counts = Counter()
    tweet_links = []

    now = datetime.utcnow()
    since_time = now - timedelta(hours=2)
    query = f'{target_hashtag} since:{since_time.date()} lang:en'

    logger.info(f"Выполняем запрос: {query}")

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
            logger.error(f"Попытка {attempt} не удалась: {str(e)}")
            if attempt < retries:
                logger.info(f"Повтор через {wait_time} секунд...")
                time.sleep(wait_time)
            else:
                raise


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Укажи хэштег, например: /analyze #dota")
            return

        hashtag = context.args[0]
        if not hashtag.startswith("#"):
            hashtag = "#" + hashtag

        await update.message.reply_text(f"🔍 Ищем твиты с {hashtag} за последние 2 часа...")

        top_hashtags, tweet_links = analyze_hashtags_and_collect_links(hashtag)

        if top_hashtags:
            response = f"📊 Топ-10 хэштегов вместе с {hashtag}:\n"
            for tag, count in top_hashtags:
                response += f"{tag}: {count} раз\n"
        else:
            response = "❌ Не найдено связанных хэштегов."

        await update.message.reply_text(response)

        if tweet_links:
            links_response = "🔗 Последние твиты:\n" + "\n".join(tweet_links)
            await update.message.reply_text(links_response)
        else:
            await update.message.reply_text("😕 Твиты не найдены.")
    except Exception as e:
        logger.error(f"Ошибка в /analyze: {str(e)}")
        await update.message.reply_text(f"Произошла ошибка: {str(e)}")


def main():
    token = "7976774747:AAEqZ02YI-SuWkv_X1ZXJTHtw5E51HcO51g"
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))

    logger.info("Бот запущен.")
    app.run_polling()


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
