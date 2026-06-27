import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os

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

    # الحدث عند اختيار المنصة
    async def callback(self, interaction: discord.Interaction):
        platform = self.values[0]
        
        # نرد على المستخدم برسالة مخفية نطلب منه الرابط
        await interaction.response.send_message(f"🔗 أرسل رابط **{platform}** هنا في الشات الآن (لديك 60 ثانية):", ephemeral=True)

        # دالة للتحقق أن الرسالة جاية من نفس الشخص وتحتوي على رابط
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and "http" in m.content

        try:
            # انتظار الرابط من المستخدم
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            url = msg.content
            
            status_msg = await msg.reply(f"⏳ جاري معالجة رابط {platform} وتحميل المقطع، لحظات...")
            
            # استدعاء دالة التحميل
            file_path = await self.download_video(url)

            if file_path == "size_limit":
                await status_msg.edit(content="❌ المقطع يتجاوز 25 ميجابايت (الحد الأقصى لديسكورد) ولا يمكن إرساله.")
            elif file_path:
                # إرسال المقطع إذا تم التحميل بنجاح
                file = discord.File(file_path)
                await msg.reply(file=file)
                await status_msg.delete()
                
                # حذف الملف من الخادم بعد الإرسال لتوفير المساحة
                os.remove(file_path) 
            else:
                await status_msg.edit(content="❌ فشل التحميل. الأسباب المحتملة:\n1. الحساب خاص (Private).\n2. المنصة تمنع التحميل حالياً.\n3. الرابط غير صحيح.")
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏳ انتهى الوقت! لم تقم بإرسال الرابط. يرجى إعادة المحاولة من المنيو.", ephemeral=True)

    # 2. دالة التحميل الفعلية باستخدام yt-dlp
    async def download_video(self, url):
        # نشغل التحميل في مسار منفصل (Thread) عشان ما يعلق البوت على باقي الأعضاء
        def yt_dlp_sync():
            # إعدادات المكتبة (جلب أفضل جودة بحجم أقل من 25 ميجا بصيغة mp4)
            ydl_opts = {
                'format': 'b[ext=mp4][filesize<25M]/b[filesize<25M]/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'quiet': True,
                'noplaylist': True,
            }
            
            # إنشاء مجلد التحميلات إذا مو موجود
            if not os.path.exists('downloads'):
                os.makedirs('downloads')
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    # التحقق الفعلي من الحجم قبل الإرسال (تحسباً لأي خطأ)
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

        # تشغيل الدالة بشكل غير متزامن
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

    # الأمر اللي يظهر المنيو للأعضاء
    @commands.command(name="media", aliases=["dl", "تحميل"])
    async def media_menu(self, ctx):
        embed = discord.Embed(
            title="🎥 محطة تحميل المقاطع",
            description="اختر المنصة من القائمة المنسدلة بالأسفل، ثم أرسل الرابط.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, view=DownloadView(self.bot))

async def setup(bot):
    await bot.add_cog(MediaDownloader(bot))