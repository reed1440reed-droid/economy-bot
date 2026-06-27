import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os

# المودال الجديد الذي سيظهر للمستخدم لإدخال الرابط
class LinkModal(discord.ui.Modal, title="إدخال الرابط"):
    url = discord.ui.TextInput(
        label="رابط المقطع",
        style=discord.TextStyle.paragraph,
        placeholder="ضع الرابط هنا...",
        required=True,
    )

    def __init__(self, select_menu):
        super().__init__()
        self.select_menu = select_menu

    async def on_submit(self, interaction: discord.Interaction):
        platform = self.select_menu.values[0]
        status_msg = await interaction.response.send_message(f"⏳ جاري معالجة رابط {platform} وتحميل المقطع، لحظات...", ephemeral=True)
        
        # استدعاء دالة التحميل من الكلاس الأصلي
        file_path = await self.select_menu.download_video(self.url.value)

        if file_path == "size_limit":
            await interaction.followup.send("❌ المقطع يتجاوز 25 ميجابايت (الحد الأقصى لديسكورد) ولا يمكن إرساله.", ephemeral=True)
        elif file_path:
            file = discord.File(file_path)
            await interaction.followup.send(file=file, ephemeral=False)
            os.remove(file_path) 
        else:
            await interaction.followup.send("❌ فشل التحميل. الأسباب المحتملة:\n1. الحساب خاص (Private).\n2. المنصة تمنع التحميل حالياً.\n3. الرابط غير صحيح.", ephemeral=True)

# 1. كلاس القائمة المنسدلة (المنيو)
class DownloadSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="يوتيوب", description="تحميل مقطع يوتيوب أو Shorts", emoji="🟥", value="youtube"),
            discord.SelectOption(label="تيك توك", description="تحميل مقطع بدون علامة مائية", emoji="⬛", value="tiktok"),
            discord.SelectOption(label="انستغرام", description="تحميل Reels أو مقاطع عامة", emoji="🟪", value="instagram"),
            discord.SelectOption(label="سناب شات", description="تحميل مقاطع Spotlight العامة", emoji="🟨", value="snapchat")
        ]
        super().__init__(placeholder="📥 اختر المنصة لتحميل المقطع...", min_values=1, max_values=1, options=options)

    # الحدث عند اختيار المنصة (تعديل: فتح المودال بدلاً من الانتظار)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LinkModal(self))

    # 2. دالة التحميل الفعلية باستخدام yt-dlp
    async def download_video(self, url):
        def yt_dlp_sync():
            ydl_opts = {
                'format': 'b[ext=mp4][filesize<25M]/b[filesize<25M]/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'quiet': True,
                'noplaylist': True,
            }
            if not os.path.exists('downloads'):
                os.makedirs('downloads')
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    if os.path.getsize(filename) > 25 * 1024 * 1024:
                        os.remove(filename)
                        return "size_limit"
                    return filename
                except yt_dlp.utils.DownloadError as e:
                    if "filesize" in str(e).lower() or "too large" in str(e).lower():
                        return "size_limit"
                    return None
                except Exception:
                    return None

        return await asyncio.to_thread(yt_dlp_sync)

# 3. حاوية المنيو
class DownloadView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(DownloadSelect(bot))

# 4. الكوج الأساسي
class MediaDownloader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="media", aliases=["dl", "تحميل"])
    async def media_menu(self, ctx):
        embed = discord.Embed(
            title="🎥 محطة تحميل المقاطع",
            description="اختر المنصة من القائمة المنسدلة بالأسفل، ثم ضع الرابط في النافذة.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, view=DownloadView(self.bot))

async def setup(bot):
    await bot.add_cog(MediaDownloader(bot))