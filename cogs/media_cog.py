import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os

# 1. كلاس المودال (النافذة المنبثقة) - هنا كامل المنطق والمعالجة
class LinkModal(discord.ui.Modal, title="أدخل الرابط لتحميل المقطع"):
    url = discord.ui.TextInput(
        label="ضع رابط المقطع هنا",
        style=discord.TextStyle.paragraph,
        placeholder="رابط يوتيوب، تيك توك، انستغرام، أو سناب شات...",
        required=True,
    )

    def __init__(self, bot, platform):
        super().__init__()
        self.bot = bot
        self.platform = platform

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"⏳ جاري معالجة {self.platform}، انتظر قليلاً...", ephemeral=True)
        
        # استدعاء دالة التحميل في مسار منفصل
        file_path = await self.download_video(self.url.value)

        if file_path == "size_limit":
            await interaction.followup.send("❌ المقطع يتجاوز 25 ميجابايت (الحد المسموح في ديسكورد).", ephemeral=True)
        elif file_path and os.path.exists(file_path):
            await interaction.followup.send(file=discord.File(file_path))
            os.remove(file_path) # حذف بعد الإرسال
        else:
            await interaction.followup.send("❌ فشل التحميل. تأكد من أن الرابط صحيح أو الحساب عام (ليس خاصاً).", ephemeral=True)

    def download_video(self, url):
        if not os.path.exists('downloads'): os.makedirs('downloads')
        
        # إعدادات المكتبة (تحجيم المقطع ليكون تحت 25 ميجا)
        ydl_opts = {
            'format': 'best[filesize<25M]/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # التحقق النهائي من الحجم قبل الإرسال
                if os.path.getsize(filename) > 25 * 1024 * 1024:
                    os.remove(filename)
                    return "size_limit"
                return filename
            except Exception as e:
                print(f"Error: {e}")
                return None

# 2. كلاس المنيو (الذي يفتح المودال)
class DownloadSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="يوتيوب", description="تحميل يوتيوب وشورتس", emoji="🟥", value="youtube"),
            discord.SelectOption(label="تيك توك", description="بدون علامة مائية", emoji="⬛", value="tiktok"),
            discord.SelectOption(label="انستغرام", description="Reels ومقاطع", emoji="🟪", value="instagram"),
            discord.SelectOption(label="سناب شات", description="تحميل Spotlight", emoji="🟨", value="snapchat")
        ]
        super().__init__(placeholder="📥 اختر المنصة للتحميل...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LinkModal(self.bot, self.values[0]))

class DownloadView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(DownloadSelect(bot))

# 3. الكوج الأساسي
class MediaDownloader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="media")
    async def media_menu(self, ctx):
        embed = discord.Embed(
            title="🎥 محطة تحميل المقاطع",
            description="اختر المنصة من القائمة، ثم ضع الرابط في النافذة التي ستظهر لك.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, view=DownloadView(self.bot))

async def setup(bot):
    await bot.add_cog(MediaDownloader(bot))