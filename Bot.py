import discord
import os  # <--- ต้องมีบรรทัดนี้!
from discord import app_commands
from datetime import datetime
from flask import Flask
from threading import Thread

# --- ระบบ Web Server สำหรับ UptimeRobot ---
app = Flask('')
@app.route('/')
def home():
    return "I'm alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ================= ตั้งค่า ID ห้อง และ คำห้ามใช้ =================
TOKEN = os.getenv('DISCORD_TOKEN')
SETUP_CHANNEL_ID = 1491787842790096997  # ห้องสำหรับกดปุ่มแจ้งลา
LOG_CHANNEL_ID = 1499440045743149147    # ห้องสำหรับรับข้อมูล

# ใส่คำที่ต้องการดักไว้ที่นี่ (บอทจะไม่เอาไปโชว์ให้คนใช้เห็น)
BANNED_WORDS = ["ขี้เกรียจ", "เงี่ยน", "ไม่อยากมา", "เบื่อ", "เซ็ง","กินเหล้า"] 
# =============================================================

class LeaveModal(discord.ui.Modal, title='แบบฟอร์มการแจ้งลา'):
    leave_type = discord.ui.TextInput(
        label='ประเภทการลา',
        placeholder='ระบุประเภทการลาของมึง...',
        required=True
    )
    
    reason = discord.ui.TextInput(
        label='สาเหตุการลา',
        style=discord.TextStyle.long,
        placeholder='อธิบายรายละเอียดการลา...', # ไม่แสดงคำห้ามใช้แล้ว
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        reason_text = self.reason.value
        
        # ตรวจสอบคำห้ามใช้แบบเงียบๆ
        if any(word in reason_text for word in BANNED_WORDS):
            # แสดงแค่ข้อความเตือนตามที่คุณต้องการ ไม่บอกว่าคำไหน
            await interaction.response.send_message("❌ **ลาดีๆสัสเดี๋ยวตบหน้าหรอก** ไปตายไป", ephemeral=True)
            return

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        
        if log_channel:
            embed = discord.Embed(
                title="📋 รายงานการแจ้งลาใหม่",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(name="👤 ผู้แจ้งลา", value=f"{interaction.user.mention}", inline=False)
            embed.add_field(name="📂 ประเภท", value=f"```\n{self.leave_type.value}\n```", inline=True)
            embed.add_field(name="📝 สาเหตุ", value=f"```\n{self.reason.value}\n```", inline=False)
            
            await log_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ ส่งใบลาเรียบร้อยแล้ว!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ เกิดข้อผิดพลาด: ไม่พบห้องรับข้อมูล", ephemeral=True)

class LeaveView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='ลาทำ💩อะไร', style=discord.ButtonStyle.danger, custom_id='persistent_leave_button')
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LeaveModal())

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(LeaveView())

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.tree.sync()

bot = MyBot()

@bot.tree.command(name="setup_leave", description="สร้างปุ่มแจ้งลา")
@app_commands.checks.has_permissions(administrator=True)
async def setup_leave(interaction: discord.Interaction):
    if interaction.channel_id != SETUP_CHANNEL_ID:
        await interaction.response.send_message(f"❌ กรุณาใช้คำสั่งในห้อง <#{SETUP_CHANNEL_ID}>", ephemeral=True)
        return

    embed = discord.Embed(
        title="📝 ระบบเเจ้งลา",
        description="กรุณากดปุ่มด้านล่าง",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=LeaveView())

bot.run(TOKEN)
