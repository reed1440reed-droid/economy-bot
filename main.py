import discord
from discord.ext import commands
import aiosqlite
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # قائمة الأوامر المتاحة بدون برفكس
    commands_list = ["كشف", "توب", "راتب", "رصيد", "أسعار", "شراء", "بيع", "هدية"]
    
    if message.content.strip() in commands_list:
        ctx = await bot.get_context(message)
        command = bot.get_command(message.content.strip())
        if command:
            await bot.invoke(ctx)
            return

    await bot.process_commands(message)

# (بقية كود الـ on_ready لتحميل الـ Cogs وإنشاء الجداول كما فعلنا سابقاً)
@bot.event
async def on_ready():
    bot.db = await aiosqlite.connect("database.db")
    # ... (كود إنشاء الجداول الذي كتبناه سابقاً)
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
    print(f'Bot is online as {bot.user.name}')

bot.run(os.getenv('DISCORD_TOKEN'))