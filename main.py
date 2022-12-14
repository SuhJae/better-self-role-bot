# imports
import configparser
import platform
import time

import nextcord
import redis
from nextcord import Interaction
from nextcord.ext import commands

# load config & language
config = configparser.ConfigParser()
config.read('config.ini')
lang = configparser.ConfigParser()
lang.read('language.ini')

token = config['CREDENTIALS']['token']
owner_id = str(config['CREDENTIALS']['owner_id'])
prefix = config['SETTINGS']['prefix']
status = config['SETTINGS']['status']
status_message = config['SETTINGS']['status_message']
status_type = config['SETTINGS']['status_type']
host = config['REDIS']['host']
port = config['REDIS']['port']
password = config['REDIS']['password']
db = config['REDIS']['db']

# check config
error_count = 0

if len(prefix) > 1:
    print('Error: Prefix must be only one character.')
    error_count += 1

if status not in ['online', 'idle', 'dnd', 'invisible']:
    print('Error: Status must be one of online, idle, dnd, or invisible.')
    error_count += 1

if status_type not in ['playing', 'streaming', 'listening', 'watching']:
    print('Error: Status type must be one of playing, streaming, listening, or watching.')
    error_count += 1

if len(status_message) > 128:
    print('Error: Status message must be less than 128 characters.')
    error_count += 1

if error_count > 0:
    print('Please change the config file (config.ini) and try again.')
    print('Exiting in 5 seconds...')
    time.sleep(5)
    exit()

# check redis connection
try:
    print(f'Connecting to Redis... ({host}:{port} Database: {db})')
    r = redis.Redis(host=host, port=port, password=password, decode_responses=True, db=db)
    r.ping()
    print(f"Connected to redis.")
except:
    print('Error: Could not connect to Redis server.')
    print('Please change the config file (config.ini) and try again.')
    print('Exiting in 5 seconds...')
    time.sleep(5)
    exit()

# discord setup
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

client = commands.Bot(command_prefix=prefix, intents=intents)


# Bot startup
@client.event
async def on_ready():
    # set status
    if status_type == 'playing':
        await client.change_presence(activity=nextcord.Game(name=status_message), status=status)
    elif status_type == 'streaming':
        await client.change_presence(activity=nextcord.Streaming(name=status_message, url='https://twich.tv'),
                                     status=status)
    elif status_type == 'listening':
        await client.change_presence(
            activity=nextcord.Activity(type=nextcord.ActivityType.listening, name=status_message), status=status)
    elif status_type == 'watching':
        await client.change_presence(
            activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=status_message), status=status)
    # print startup message
    owner_name = await client.fetch_user(owner_id)
    print('======================================')
    print(f'Logged in as {client.user.name}#{client.user.discriminator} ({client.user.id})')
    print(f"Owner: {owner_name} ({owner_id})")
    print(f'Currenly running nextcord {nextcord.__version__} on python {platform.python_version()}')
    print('======================================')

@client.slash_command(name='test', description='test command', dm_permission=False, default_member_permissions=8)
async def test(interaction: Interaction):
    selection = [
        nextcord.SelectOption(label='Option 1', value='1', description='Option 1'),
    ]

    view = DropdownMenu(selection)

    await interaction.response.send_message('test', view=view)

@client.slash_command(name='create', description='Create new self assignable roles', dm_permission=False, default_member_permissions=8)
async def create(interaction: Interaction,
                 channel: nextcord.TextChannel = nextcord.SlashOption(
                    description='Channel where the role dropdown will be',
                    required=True
                 ),
                 name: str = nextcord.SlashOption(
                     description='Name of the placeholder of the dropdown',
                     required=False
                 ),
                ):
    selection = [
        nextcord.SelectOption(label='No role added', value='0', description='Add a role to the dropdown using /addrole')
    ]
    await channel.send(view=DropdownMenu(selection))

    await interaction.response.send_message(f'Dropdown created at {channel.mention}', ephemeral=True)


class Dropdown(nextcord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder='Select a role', options=options)
    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(f'You selected {self.values}')

class DropdownMenu(nextcord.ui.View):
    def __init__(self, options):
        super().__init__()
        self.add_item(Dropdown(options))



client.run(token)