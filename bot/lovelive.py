import aiohttp
import discord
import random
import requests
import logging

from bs4 import BeautifulSoup

from .common import *

logger = logging.getLogger('root.lovelive')

class LoveLive:
	def __init__(self):
		pass
    
	async def cmd_cardinfo(self, message, card_id, *args, internal=False):
		'''
		Show info of a LLSIF card by id (idolized if defined)
		Command group: Love Live!
		Usage: {command_prefix}cardinfo card_id [idlz / idolized]
		Example:
			{command_prefix}cardinfo 2145
			{command_prefix}cardinfo 2145 idlz
		'''
		promo = ''
		getinfo = 'card_image'
		card_id = str(card_id)

		if not card_id.isdigit():
			await message.channel.send('```prolog\nPlease type card id properly```')
			return
		else:
			if args:
				if args[0].lower() in ['idlz', 'idolized']:
					getinfo = 'card_idolized_image'

		async with message.channel.typing():
			url = 'http://schoolido.lu/api/cards/%s/' % (card_id)

			async with aiohttp.ClientSession() as session:
				async with session.get(url) as r:
					if r.status == 200:
						js = await r.json()
						img = 'http:%s' % (js[getinfo])
						card_name = js['idol']['name']
						collection = js['translated_collection']
						release_date = js['release_date']
						is_promo = js['is_promo']
						attribute = js['attribute']
						ranking_attribute = js['ranking_attribute']
						if img == "http:None":
							if not internal:
								await message.channel.send('This card does not have unidolized version. Here\'s the idolized.')
							img = 'http:%s' % (js['card_idolized_image'])
						if is_promo == 'True':
							promo = 'Promo Card\n'
						else:
							promo = ''

						await message.channel.send(
							f'{img}\n```prolog\nCard No. {card_id}\nName: {card_name}\nCollection: {collection}\n' +
							f'Released date: {release_date}\n{promo}#{ranking_attribute} best {attribute} card```\n'
						)
						return 1
					else:
						if not internal:
							await message.channel.send('```prolog\nNetwork timed out or card not found.```')
						return 0

	async def cmd_randomcard(self, message, *args):
		'''
		Show info of a random LLSIF card by idol / rarity
		Command group: Love Live!
		Usage:
			{command_prefix}randomcard [idol] [rarity]
			- idol: 
				maki, rin, hanayo, kotori, honoka, umi, eli, nozomi, nico,
				ruby, hanamaru, yoshiko, yohane, you, chika, riko, mari, kanan, dia,
				ayumu, ai, setsuna, kanata, karin, emma, rina, shizuku, kasumi,
				and some support characters
			- rarity: R, SR, SSR, UR
		Example:
			{command_prefix}randomcard
			{command_prefix}randomcard kotori
			{command_prefix}randomcard ur
			{command_prefix}randomcard kotori ur
		'''
		if not args:
			found = False
			while not found:
				random_id = random.randint(1, self.max_sif_cards)
				r = await self.cmd_cardinfo(message, random_id, internal=True)
				if r:
					return

		url = 'http://schoolido.lu/api/cardids/?'

		args = list(args)

		while args:
			query = args.pop(0)
			if query is not None:
				query = query.lower()
				if query in SIF_NAME_LIST:
					url += 'name=%s&' % SIF_IDOL_NAMES[query]
					logger.debug('Set url: %s' % url)
				
				if query in ['r', 'sr', 'ssr', 'ur']:
					url += 'rarity=%s&' % query
					logger.debug('Set url: %s' % url)
			
		async with message.channel.typing():
			async with aiohttp.ClientSession() as session:
				async with session.get(url) as r:
					if r.status == 200:
						js = await r.json()
						card_num = random.choice(js)
						logger.debug('Random card: %s' % card_num)
						await self.cmd_cardinfo(message, card_num)
						return
					else:
						logger.error('Error: %s' % r.status)
						await message.channel.send('```prolog\nHTTP Error %s. Please try again later.```' % r.status)
						return
	
	async def cmd_idolinfo(self, message, query, *args):
		'''
		Show info of a Love Live! Idol
		Command group: Love Live!
		Usage:
			{command_prefix}idolinfo [name]
			- name:
				maki, rin, hanayo, kotori, honoka, umi, eli, nozomi, nico,
				ruby, hanamaru, yoshiko, yohane, you, chika, riko, mari, kanan, dia,
				ayumu, ai, setsuna, kanata, karin, emma, rina, shizuku, kasumi
		Example:
			{command_prefix}idolinfo kotori
		'''
		logger.debug("Searched for %s" % (query))

		if query not in SIF_NAME_LIST:
			await message.channel.send('```prolog\nIdol not found.```')
			return

		idol = SIF_IDOL_NAMES[query]

		url = 'http://schoolido.lu/api/idols/%s/' % (idol)
		logger.debug("Getting info from %s" % (url))

		async with aiohttp.ClientSession() as session:
			async with session.get(url) as r:
				if r.status == 200:
					js = await r.json()

					name = js['name']
					jpname = js['japanese_name']
					age = js['age']
					school = js['school']
					birthday = js['birthday']
					astrological_sign = js['astrological_sign']
					blood = js['blood']
					height = js['height']
					measurements = js['measurements']
					favorite_food = js['favorite_food']
					least_favorite_food = js['least_favorite_food']
					hobbies = js['hobbies']
					attribute = js['attribute']
					year = js['year']
					main_unit = js['main_unit']
					sub_unit = js['sub_unit']

					try:
						cv_name = js['cv']['name']
					except:
						cv_name = js['cv']
					try:
						cv_nickname = js['cv']['nickname']
					except:
						cv_nickname = js['cv']

					summary = js['summary']
					chibi = js['chibi_small']

				else:
					await message.channel.send('```prolog\nError occurs. Please try again later.```')

		e = discord.Embed(title="Idol information", type="rich", color=SIF_COLOR_LIST[name])

		e.set_thumbnail(url="%s" % chibi)

		e.add_field(name="Name", value=name, inline=True)
		e.add_field(name="Japanese", value=jpname, inline=True)
		e.add_field(name="Age", value=age, inline=True)

		e.add_field(name="Birthday", value=birthday, inline=True)
		e.add_field(name="Sign", value=astrological_sign, inline=True)
		e.add_field(name="Year", value=year, inline=True)
		e.add_field(name="School", value=school, inline=True)

		e.add_field(name="Blood type", value=blood, inline=True)
		e.add_field(name="Height", value=height, inline=True)
		e.add_field(name="Measurements", value=measurements, inline=True)

		e.add_field(name="Favourite food", value=favorite_food, inline=True)
		e.add_field(name="Dislike food", value=least_favorite_food, inline=True)
		
		e.add_field(name="Hobbies", value=hobbies, inline=True)
		e.add_field(name="Main unit", value=main_unit, inline=True)
		e.add_field(name="Sub unit", value=sub_unit, inline=True)

		e.add_field(name="Summary", value=summary, inline=False)

		e.add_field(name="CV", value=cv_name, inline=True)
		e.add_field(name="Nickname", value=cv_nickname, inline=True)

		await message.channel.send('```css\nYou searched for "%s"\n```' % (query), embed=e)

	async def cmd_lyrics(self, message, query, *args):
		'''
		Search for lyrics of a Love Live! song
		Command group: Love Live!
		Usage:
			{command_prefix}lyrics [language] [song_name]
			- language: romaji by default
				+ kanji / japanese / jap / ja
				+ english / eng / en
		Example:
			{command_prefix}lyrics spicaterrible
			{command_prefix}lyrics kanji spicaterrible
			{command_prefix}lyrics en spicaterrible
		'''
		i = 0

		query = query.lower()

		if query in ['kanji', 'japanese', 'jap', 'ja']:
			i = 1
		elif query in ['english', 'eng', 'en']:
			i = 2

		if i != 0:
			query = ' '.join(args)
		else:
			query = ' '.join([query, *args])

		song_list = os.path.join('game_cache', 'song_list')
		if not os.path.exists(song_list):
			songs_available = self._create_song_list()
		else:
			with open(song_list, mode='r') as f:
				songs_available = f.readlines()
		
		found = False
		for song_url in songs_available:
			if query.replace(' ', '_') in song_url.lower():
				found = True
				r = requests.get(song_url.strip())
				soup = BeautifulSoup(r.content, 'html5lib')
				song_name = soup.find('h1', {'class': 'page-header__title'}).text.strip()

				try:
					poem = soup.find_all('div', {'class': 'poem'})[i]
				except IndexError:
					poem = soup.find_all('div', {'class': 'poem'})[0]

				lyrics = poem.text.strip()

				await send_long_message(message.channel, f'Here you go:\n```css\n{lyrics}```', prefix='```css', suffix='```', sep='\n')
		
		if not found:
			await message.channel.send('```prolog\nHm... I can\'t find this song in the database (´ヘ｀()```')
	