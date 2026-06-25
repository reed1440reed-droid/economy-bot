import discord
from discord.ext import commands
import aiosqlite
import os
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is online! Logged in as {bot.user.name}')
    
    # إنشاء اتصال دائم بقاعدة البيانات وربطه بالبوت
    bot.db = await aiosqlite.connect("database.db")
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            wallet INTEGER DEFAULT 0,
            bank INTEGER DEFAULT 0
        )
    """)
    await bot.db.commit()

    # تحميل ملفات الأوامر (Cogs)
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Loaded {filename}")

# سحب التوكن بأمان وتشغيل البوت
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    print("❌ خطأ: لم يتم العثور على التوكن! تأكد من وجود ملف .env")
else:
    bot.run(TOKEN)