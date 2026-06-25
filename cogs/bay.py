import discord
from discord.ext import commands
import random

class Bay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.items = {
            "سيارة": 50000, "طيارة": 500000, "جزيرة": 1000000, 
            "بيت": 200000, "مستشفى": 750000, "يخت": 300000, "أسهم": 10000
        }

    # الأوامر (أسعار، شراء، بيع، هدية)
    # تأكد من استخدام self.bot.db في جميع عمليات قاعدة البيانات
    
    @commands.command(name="أسعار")
    async def prices(self, ctx):
        embed = discord.Embed(title="📊 بورصة السوق اليومية", color=0x000000)
        for item, price in self.items.items():
            new_price = int(price * random.uniform(0.9, 1.1))
            embed.add_field(name=item, value=f"`{new_price:,}` عملة", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="شراء")
    async def buy(self, ctx):
        # ... (نفس الكود السابق الذي يحتوي على قائمة Select) ...
        # تأكد فقط من استخدام await self.bot.db.execute(...)
        pass

    @commands.command(name="بيع")
    async def sell(self, ctx):
        # ... (نفس الكود السابق) ...
        pass

    @commands.command(name="هدية")
    @commands.cooldown(1, 43200, commands.BucketType.user)
    async def gift(self, ctx, member: discord.Member, amount: int):
        # تأكد من خصم المبلغ وإضافته عبر await self.bot.db.execute
        pass

async def setup(bot):
    await bot.add_cog(Bay(bot))