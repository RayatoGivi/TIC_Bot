# imports
import discord
from discord.ext import commands
import datetime
from datetime import datetime
import mysql.connector

# create bot
warnings = {}
admin_users = []

intents = discord.Intents.all()
intents.members = True

client = commands.Bot(command_prefix='/', intents=intents)
client.remove_command('help')
prefix = '/'

# connect to db mysql
mydb = mysql.connector.connect(
    host="YOUR_URL_HOST_DB",
    user="YOUR_USERNAME_DB",
    password="YOUR_PASSWORD_DB",
    database="YOUR_NAME_DB"
)

# create table in db
mycursor = mydb.cursor()
mycursor.execute(
    "create table if not exists activity_data (user_id bigint, date date, channel_id bigint, duration int)")

channel_entry_time = {}  # global name channel_entry_time


@client.event
async def on_ready():
    print('Entry as:\n{0.user.name}\n{0.user.id}'.format(client))


@client.event
async def on_voice_state_update(member, before, after):
    global channel_entry_time

    if before.channel and not after.channel:
        if member.id in channel_entry_time:
            duration = (datetime.now() - channel_entry_time[member.id]).total_seconds()
            current_date = datetime.now().strftime('%d.%m.%y')

            channel_id = before.channel.id

            mycursor.execute("select * from activity_data where user_id = %s and date = %s and channel_id = %s",
                             (member.id, current_date, channel_id))
            result = mycursor.fetchall()

            if len(result) > 0:
                duration += result[0][3]
                mycursor.execute(
                    "update activity_data set duration = %s where user_id = %s and date = %s and channel_id = %s",
                    (duration, member.id, current_date, channel_id))
            else:
                mycursor.execute(
                    "insert into activity_data (user_id, date, channel_id, duration) values (%s, %s, %s, %s)",
                    (member.id, current_date, channel_id, duration))

            mydb.commit()

        channel_entry_time[member.id] = datetime.now()

    elif after.channel and not before.channel:
        channel_entry_time[member.id] = datetime.now()


@client.command()
async def activity(ctx, user: discord.User, date: str):
    user_id = user.id
    current_date = datetime.now().strftime('%d.%m.%y')

    mycursor.execute("select channel_id, duration from activity_data where user_id = %s and date = %s", (user_id, date))
    result = mycursor.fetchall()

    if len(result) == 0:
        await ctx.send("No activity find for this date.")
        return

    total_duration = 0

    activity_message = f"**Activity** **{user.global_name}** **{date}:**\n"

    for row in result:
        channel_id = row[0]
        duration = row[1]

        channel = ctx.guild.get_channel(channel_id)
        if channel:
            duration_str = seconds_to_hhmm(duration)
            activity_message += f"```{channel.name}, {duration_str}\n```"
            total_duration += duration

    total_duration_str = seconds_to_hhmm(total_duration)

    embed = discord.Embed(
        title=f"Bot» Member {user.display_name}",
        description=f"**Date**: **{date}**\n**All activity**: **{total_duration_str}**",
        color=discord.Color.blue()
    )

    embed.add_field(name="Member online in channels:", value=activity_message, inline=False)

    await ctx.send(embed=embed)


# function for formatting time 'hours:minutes:seconds'
def seconds_to_hhmm(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    sec = round(seconds % 60)
    return f"{hours} часов, {minutes} мин., {sec} секунд."


@client.event
async def on_ready():
    print('Bot sucssefully started!')


client.run('YOUR_TOKEN')
