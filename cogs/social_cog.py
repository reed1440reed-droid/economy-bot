import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import aiohttp
import xml.etree.ElementTree as ET

MY_GUILD = discord.Object(id=1439839910172295303) 

class SocialNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "social_trackers.db"
        # تشغيل الفحص التلقائي في الخلفية
        self.check_socials.start()

    async def cog_load(self):
        # إنشاء جدول قاعدة البيانات لحفظ الحسابات المرتبطة
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trackers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT,
                    account_id TEXT,
                    channel_id INTEGER,
                    last_post_id TEXT
                )
            """)
            await db.commit()

    def cog_unload(self):
        self.check_socials.cancel()

    # ================= 1. أوامر الإعداد (Setup) =================
    
    # إنشاء مجموعة أوامر (Group) باسم /social
    social_group = app_commands.Group(name="social", description="إدارة إشعارات يوتيوب وتويتش وتيك توك", default_permissions=discord.Permissions(administrator=True))

    @social_group.command(name="add", description="إضافة حساب جديد ليقوم البوت بنشر جديده تلقائياً")
    @app_commands.describe(
        platform="المنصة (يوتيوب، تويتش، تيك توك)",
        account_id="آيدي القناة (Channel ID) ليوتيوب، أو اسم المستخدم للمنصات الأخرى",
        channel="الروم الذي سيرسل فيه البوت الإشعار"
    )
    @app_commands.choices(platform=[
        app_commands.Choice(name="🔴 يوتيوب (YouTube)", value="youtube"),
        app_commands.Choice(name="🟣 تويتش (Twitch)", value="twitch"),
        app_commands.Choice(name="⚫ تيك توك (TikTok)", value="tiktok")
    ])
    async def add_tracker(self, interaction: discord.Interaction, platform: app_commands.Choice[str], account_id: str, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # التحقق مما إذا كان الحساب مضافاً مسبقاً لنفس الروم
            async with db.execute("SELECT id FROM trackers WHERE platform = ? AND account_id = ? AND channel_id = ?", (platform.value, account_id, channel.id)) as cursor:
                if await cursor.fetchone():
                    return await interaction.followup.send("❌ هذا الحساب مضاف بالفعل في هذا الروم!", ephemeral=True)
            
            # إضافة الحساب لقاعدة البيانات
            await db.execute("INSERT INTO trackers (platform, account_id, channel_id, last_post_id) VALUES (?, ?, ?, ?)", (platform.value, account_id, channel.id, "NONE"))
            await db.commit()

        await interaction.followup.send(f"✅ تم ربط حساب **{platform.name}** (`{account_id}`) بنجاح! سيتم نشر المقاطع الجديدة في {channel.mention}.", ephemeral=True)

    @social_group.command(name="remove", description="حذف حساب من نظام الإشعارات")
    @app_commands.describe(account_id="آيدي القناة أو اسم المستخدم المراد حذفه")
    async def remove_tracker(self, interaction: discord.Interaction, account_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM trackers WHERE account_id = ?", (account_id,))
            await db.commit()
        await interaction.response.send_message(f"🗑️ تم حذف إشعارات الحساب `{account_id}` بنجاح.", ephemeral=True)

    # ================= 2. محرك الفحص التلقائي (الخلفية) =================
    
    # البوت سيفحص كل 5 دقائق للبحث عن مقاطع أو بثوث جديدة
    @tasks.loop(minutes=5)
    async def check_socials(self):
        await self.bot.wait_until_ready()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id, platform, account_id, channel_id, last_post_id FROM trackers") as cursor:
                trackers = await cursor.fetchall()

        for tracker in trackers:
            tracker_id, platform, account_id, channel_id, last_post_id = tracker
            
            # محاولة جلب الروم، إذا تم حذفه من الديسكورد، نتجاوزه
            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue

            if platform == "youtube":
                await self.check_youtube(db, tracker_id, account_id, channel, last_post_id)
            elif platform == "twitch":
                # يحتاج برمجة API تويتش هنا
                pass
            elif platform == "tiktok":
                # يحتاج برمجة API تيك توك هنا
                pass

    # ================= 3. نظام فحص يوتيوب الفعلي =================
    
    async def check_youtube(self, db, tracker_id, channel_id, discord_channel, last_post_id):
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return # فشل في جلب البيانات
                    
                    xml_data = await response.text()
                    
            # تحليل الـ XML الخاص بيوتيوب
            root = ET.fromstring(xml_data)
            
            # مساحات الأسماء (Namespaces) الخاصة بيوتيوب
            ns = {'yt': 'http://www.youtube.com/xml/schemas/2015', 'media': 'http://search.yahoo.com/mrss/', 'default': 'http://www.w3.org/2005/Atom'}
            
            # جلب أحدث مقطع (أول entry في القائمة)
            entry = root.find('default:entry', ns)
            if not entry:
                return

            video_id = entry.find('yt:videoId', ns).text
            
            # إذا كان المقطع جديداً ولم يتم نشره مسبقاً
            if video_id != last_post_id:
                title = entry.find('default:title', ns).text
                video_url = entry.find('default:link', ns).attrib['href']
                
                # جلب وصف المقطع واقتطاعه لتجنب رسائل الإيرور إذا كان الوصف طويلاً جداً
                media_group = entry.find('media:group', ns)
                description = media_group.find('media:description', ns).text if media_group is not None else "بدون وصف"
                if description and len(description) > 300:
                    description = description[:300] + "...\n\n[اقرأ المزيد في المقطع]"

                # تصميم الإيمبد الاحترافي
                embed = discord.Embed(
                    title=title,
                    url=video_url,
                    description=f"**تفاصيل المقطع:**\n{description}",
                    color=discord.Color.red()
                )
                embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg") # جلب صورة المقطع (Thumbnail) بجودة عالية
                embed.set_footer(text="يوتيوب", icon_url="https://upload.wikimedia.org/wikipedia/commons/e/ef/Youtube_logo_2006.png")

                # إرسال الرسالة مع منشن @everyone خارج الإيمبد
                content = f"@everyone\n🚨 **مقطع جديد نزل الآن! لا يفوتكم!**\n{video_url}"
                await discord_channel.send(content=content, embed=embed)

                # تحديث قاعدة البيانات حتى لا ينشر نفس المقطع مرة أخرى
                async with aiosqlite.connect(self.db_path) as db_update:
                    await db_update.execute("UPDATE trackers SET last_post_id = ? WHERE id = ?", (video_id, tracker_id))
                    await db_update.commit()

        except Exception as e:
            print(f"YouTube Check Error for {channel_id}: {e}")

async def setup(bot):
    # ربط مجموعة الأوامر بالسيرفر للظهور السريع
    bot.tree.add_command(SocialNotifier.social_group, guild=MY_GUILD)
    await bot.add_cog(SocialNotifier(bot))