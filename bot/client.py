import os
import logging
import asyncio
import yaml
import shutil
import traceback
from textwrap import dedent
from inspect import signature
import datetime

import discord

from .commands import Commands, _pic_func

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s]: %(message)s'))
logger.addHandler(handler)

class MainClient(discord.Client, discord.VoiceClient, Commands):
	def __init__(self):
		self.load_config()

		for attr in self.config:
			setattr(self, attr, self.config[attr])
		
		self.playing_cardgame = False
		self.playing_lyricgame = False
		self.playing_songgame = False
		self.playing_radio = False
		self.force_stop_radio = False
		self.voice_client = None
		self.voice_channel = None
		self.music_queue = []
		self.current_song = None
		self.voice_text_channel = None
		self.loop = False
		self.music_cache_dir = os.path.join(os.getcwd(), 'audio_cache')
		pic_cmds = {
			'cmd_hug': {
				'type': 'hug',
				'target': True,
				'text': 'hugs'
			},
			'cmd_cry': {
				'type': 'cry',
				'target': False,
				'text': 'cries in the corner'
			},
			'cmd_cuddle': {
				'type': 'cuddle',
				'target': True,
				'text': 'cuddles'
			},
			'cmd_kiss': {
				'type': 'kiss',
				'target': True,
				'text': 'kisses'
			},
			'cmd_lewd': {
				'type': 'lewd',
				'target': False,
				'text': 'is feeling lewd'
			},
			'cmd_nom': {
				'type': 'nom',
				'target': False,
				'text': 'is eating something. Seems delicious'
			},
			'cmd_nyan': {
				'type': 'nyan',
				'target': False,
				'text': 'says Nyaaaaa~~~'
			},
			'cmd_owo': {
				'type': 'owo',
				'target': False,
				'text': 'feels ...?'
			},
			'cmd_pat': {
				'type': 'pat',
				'target': True,
				'text': 'pats'
			},
			'cmd_pout': {
				'type': 'pout',
				'target': False,
				'text': 'is feeling bad'
			},
			'cmd_slap': {
				'type': 'slap',
				'target': True,
				'text': 'slaps'
			},
			'cmd_smug': {
				'type': 'smug',
				'target': False,
				'text': 'smugs'
			},
			'cmd_stare': {
				'type': 'stare',
				'target': True,
				'text': 'stares at'
			},
			'cmd_tickle': {
				'type': 'tickle',
				'target': True,
				'text': 'tickles'
			},
			'cmd_triggered': {
				'type': 'triggered',
				'target': False,
				'text': 'is triggered'
			},
			'cmd_lick': {
				'type': 'lick',
				'target': True,
				'text': 'licks'
			}
		}

		for cmd in pic_cmds:
			f = _pic_func(pic_cmds[cmd])
			setattr(self, cmd, f)

		if os.path.exists('audio_cache'):
			shutil.rmtree('audio_cache')

		os.mkdir('audio_cache')

		game_cache_songs = os.path.join('game_cache', 'songs')
		if os.path.exists(game_cache_songs):
			shutil.rmtree(game_cache_songs)

		os.mkdir(game_cache_songs)

		self.check_sleep()

		return super(MainClient, self).__init__()
	
	def check_sleep(self, message=None):
		h = datetime.datetime.utcnow().hour
		active_from = int(self.config['active_from'])
		active_to = int(self.config['active_to'])
		time_zone = int(self.config['time_zone'])
		hour = h + time_zone
		if hour > 24:
			hour -= 24
		if active_to > 24:
			active_to -= 24
		if hour <= active_from and hour >= active_to:
			if message:
				asyncio.run_coroutine_threadsafe(message.channel.send(f'```css\nOh... It\'s my bedtime already? Oyasumi <3. See u at {active_from}```'), self.loop)
			print('Sleep time...')
			raise SleepException

	def check_owner(self, message):
		if str(message.author.id) == str(self.owner_id):
			return True
		return False

	def load_config(self):
		try:
			with open('config/global.yaml') as f:
				self.config = yaml.load(f, Loader=yaml.CSafeLoader)
			return
		except FileNotFoundError:
			with open('config/global_sample.yaml') as f:
				self.config = yaml.load(f, Loader=yaml.CSafeLoader)

		if 'BOT_TOKEN' in os.environ:
			self.token = os.environ['BOT_TOKEN']
		
		if 'YOUTUBE_APIKEY' in os.environ:
			self.youtube_apikey = os.environ['YOUTUBE_APIKEY']

		if 'OWNER_ID' in os.environ:
			self.owner_id = os.environ['OWNER_ID']

	def on_ready(self):
		print('Logged on as %s' % (self.user))
		print('Set Prefix: %s' % self.prefix)
		print('Connected to:')
		for guild in self.guilds:
			print(' - {0.name} ({0.id})'.format(guild))

	async def on_message(self, message):
		if not message.author.bot:
			if message.content.startswith(self.prefix):
				print('Message from {0.author}: {0.content}'.format(message))
				m = message.content[1:]
				c = m.split(' ')[0]

				if hasattr(self, 'cmd_' + c):
					cmd = getattr(self, 'cmd_' + c)

					if ' ' in message.content:
						has_args = True
						actual_params = len(m[len(c) + 1:].split(' '))
					else:
						has_args = False
						actual_params = 0

					sig = signature(cmd).parameters
					required_count = -1

					for k, v in sig.items():
						if v.kind.name == 'POSITIONAL_OR_KEYWORD':
							required_count += 1

					if required_count > actual_params:
						if c != 'help':
							doc = '```prolog\n{0}```'.format(dedent(cmd.__doc__))
							doc = doc.replace('{command_prefix}', self.prefix)
							await message.channel.send(doc)
							return

					try:
						if not has_args:
							self.check_sleep(message)
							if c == 'llradio':
								await message.channel.send('If you want another Love Live! Radio instance, consider adding another me: https://discordapp.com/api/oauth2/authorize?client_id=697328604186411018&permissions=70569024&scope=bot')
							await cmd(message, None)
						else:
							self.check_sleep(message)
							await cmd(message, *m[len(c) + 1:].split(' '))
					except Exception as e:
						try:
							errmsg = "Error: %s\n```%s```\nSend this to the bot's owner, pls :(" % (repr(e), traceback.format_exc())
							await message.channel.send(errmsg)
						except:
							pass
					
			if type(message.channel) == discord.channel.DMChannel:
				msg = f'Message from {message.author.name}#{message.author.discriminator} ({message.author.id}):\n{message.content}'
				if len(message.attachments) != 0:
					for a in message.attachments:
						msg += f'\n{a.url}'
				for guild in self.guilds:
					for member in guild.members:
						if str(member.id) == str(self.owner_id):
							await member.send(msg)
							return
