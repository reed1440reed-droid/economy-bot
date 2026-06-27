import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os

# 1. كلاس النافذة المنبثقة (Modal)
class LinkModal(discord.ui.Modal, title="أدخل الرابط للتحميل"):
    url = discord.ui.TextInput(
        label="رابط المقطع",
        style=discord.TextStyle.paragraph,
        placeholder="ضع الرابط هنا...",
        required=True,
    )

    def __init__(self, bot, platform):
        super().__init__()
        self.bot = bot
        self.platform = platform

    async def on_submit(self, interaction: discord.Interaction):
        url = self.url.value
        await interaction.response.send_message(f"⏳ جاري معالجة رابط {self.platform}، لحظات...", ephemeral=True)
        
        # استدعاء دالة التحميل
        file_path = await self.download_video(url)

        if file_path == "size_limit":
            await interaction.followup.send("❌ المقطع يتجاوز 25 ميجابايت (الحد الأقصى لديسكورد).", ephemeral=True)
        elif file_path:
            file = discord.File(file_path)
            await interaction.followup.send(file=file)
            os.remove(file_path) # حذف بعد الإرسال
        else:
            await interaction.followup.send("❌ فشل التحميل. تأكد من أن الرابط صحيح وحساب المقطع عام.", ephemeral=True)

    async def download_video(self, url):
        def yt_dlp_sync():
            ydl_opts = {'format': 'b[ext=mp4][filesize<25M]/b[filesize<25M]/best', 'outtmpl': 'downloads/%(id)s.%(ext)s', 'quiet': True}
            if not os.path.exists('downloads'): os.makedirs('downloads')
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(info)
                except: return None
        return await asyncio.to_thread(yt_dlp_sync)

# 2. كلاس المنيو (الذي يفتح المودال)
class DownloadSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="يوتيوب", value="youtube", emoji="🟥"),
            discord.SelectOption(label="تيك توك", value="tiktok", emoji="⬛"),
            discord.SelectOption(label="انستغرام", value="instagram", emoji="🟪"),
            discord.SelectOption(label="سناب شات", value="snapchat", emoji="🟨")
        ]
        super().__init__(placeholder="📥 اختر المنصة لتحميل المقطع...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # هنا نفتح المودال بدلاً من الانتظار في الشات
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
        embed = discord.Embed(title="🎥 محطة تحميل المقاطع", description="اختر المنصة ثم أدخل الرابط في النافذة المنبثقة.", color=discord.Color.green())
        await ctx.send(embed=embed, view=DownloadView(self.bot))

async def setup(bot):
    await bot.add_cog(MediaDownloader(bot))