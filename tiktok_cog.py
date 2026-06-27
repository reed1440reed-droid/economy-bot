import discord
from discord.ext import commands
import aiohttp
import io
import re

class TikTokDownloader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ⚠️ آيدي (ID) الروم المخصص لتنزيل التيك توك فقط
        self.ALLOWED_CHANNEL_ID = 1517053489115828244  

    # دالة جلب المقطع (أصبحت داخل الكلاس)
    async def get_tiktok_video(self, url):
        """دالة لجلب المقطع بدون شعار باستخدام API خارجي"""
        api_url = f"https://www.tikwm.com/api/?url={url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('code') == 0 and 'data' in data and 'play' in data['data']:
                        video_url = data['data']['play']
                        
                        async with session.get(video_url) as vid_resp:
                            if vid_resp.status == 200:
                                return await vid_resp.read()
        return None

    # حدث قراءة الرسائل
    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. تجاهل رسائل البوت نفسه
        if message.author == self.bot.user:
            return

        # 2. التحقق من أن الرسالة أُرسلت في الروم المحدد فقط
        if message.channel.id != self.ALLOWED_CHANNEL_ID:
            return  # إذا لم تكن في الروم المحدد، يتجاهل البوت الرسالة

        # نمط للبحث عن أي رابط تيك توك داخل الرسالة
        tiktok_regex = r'(https?://(?:www\.)?(?:tiktok\.com/|vm\.tiktok\.com/|vt\.tiktok\.com/)[^\s]+)'
        match = re.search(tiktok_regex, message.content)

        if match:
            tiktok_url = match.group(1)
            
            processing_msg = await message.reply("⏳ جاري تحميل المقطع بدون شعار، لحظات...")
            video_bytes = await self.get_tiktok_video(tiktok_url)

            if video_bytes:
                # التحقق من أن حجم المقطع لا يتجاوز حد الديسكورد (25MB)
                if len(video_bytes) > 25 * 1024 * 1024:
                    await processing_msg.edit(content="❌ حجم المقطع يتجاوز 25 ميجابايت ولا يمكن إرساله مباشرة.")
                    return

                # إرسال المقطع
                file = discord.File(fp=io.BytesIO(video_bytes), filename="tiktok_video.mp4")
                await message.reply(file=file)
                await processing_msg.delete() 
                
            else:
                await processing_msg.edit(content="❌ عذراً، لم أتمكن من تحميل المقطع. تأكد من صحة الرابط.")

# الدالة الإلزامية لربط الكوج بالملف الأساسي
async def setup(bot):
    await bot.add_cog(TikTokDownloader(bot))