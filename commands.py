import re
import aiohttp
import logging
import time
import tempfile
import asyncio
import random
import urllib
import io
import shutil

from threading import Timer
from textwrap import dedent

import discord
from PIL import Image, ImageDraw, ImageFont
from player import MusicPlayer

logger = logging.getLogger('Command')

async def get_pic(img_type):
    url = "https://rra.ram.moe/i/r?type=%s" % (img_type)
    network_timeout = False

    while not network_timeout:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    js = await r.json()
                    link = js['path']
                    url = "https://rra.ram.moe%s" % (link)
                    break
                else:
                    print('Error: %s' % r.status)
                    network_timeout = True
                    return {'error': True, 'message': 'HTTP Error %s. Please try again.' % r.status}

    return {'error': False, 'url': url}

def _pic_func(func_obj):
    if func_obj['target']:
        async def target_func(message, target, *args):
            '''
            Sends a pic
            Command group: Pics
            Usage: {command_prefix}[action] [mention / text]
            Example: ~[action] / ~[action] @_Kotori_
            '''
            url = await get_pic(func_obj['type'])
            if url['error']:
                await message.channel.send(url['message'])
            else:
                if not target:
                    target = 'himself'
                if len(message.mentions) > 0:
                    target = message.mentions[0].name
                e = discord.Embed(title='{0} {1} {2}'.format(message.author.name, func_obj['text'], target))
                e.set_image(url=url['url'])
                await message.channel.send(embed=e)
        return target_func
    else:
        async def notarget_func(message, *args):
            '''
            Sends a pic
            Command group: pics
            Usage: {command_prefix}[action]
            Example: ~[action]
            '''
            url = await get_pic(func_obj['type'])
            if url['error']:
                await message.channel.send(url['message'])
            else:
                e = discord.Embed(title='{0} {1}'.format(message.author.name, func_obj['text']))
                e.set_image(url=url['url'])
                await message.channel.send(embed=e)
        return notarget_func

class Commands(MusicPlayer):
    def __init__(self):
        return super(Commands, self).__init__()

    async def cmd_setprefix(self, message, prefix, *args, **kwargs):
        '''
        Set bot's prefix
        Command group: Special
        Usage: {command_prefix}setprefix [prefix]
        Example: ~setprefix !
        '''
        self.prefix = prefix
        await message.channel.send('```Set prefix: {0}```'.format(prefix))
        print('Set prefix: %s' % (prefix))

    async def cmd_help(self, message, command, *args, **kwargs):
        '''
        Display help
        Command group: Special
        Usage: {command_prefix}help [command]
        Example: ~help / ~help setprefix
        '''
        e = discord.Embed()
        
        if not command or command == '':
            groups = {}
            async with message.channel.typing():
                for attr in dir(self):
                    if attr.startswith('cmd_'):
                        help_info = dedent(getattr(self, attr).__doc__)
                        group = re.findall('Command group: (.*)\n', help_info)[0]
                        if group not in groups:
                            groups[group] = []
                        groups[group].append(attr[4:])
                e.title = 'Command list'
                for group in groups:
                    e.add_field(name=group, value=', '.join(groups[group]), inline=False)
        
        else:
            if 'cmd_' + command in dir(self):
                e.title = command
                desc = dedent(getattr(self, 'cmd_' + command).__doc__)
                if '[action]' in desc:
                    desc = desc.replace('[action]', command)
                e.description = desc
            else:
                await message.channel.send('Command not found')
                return

        await message.channel.send(embed=e)
    
    async def cmd_say(self, message, *args):
        '''
        Make the bot say something
        Command group: Misc
        Usage: {command_prefix}say [text]
        Example: ~say Hello!
        '''
        await message.channel.send(' '.join(args))
    
    async def cmd_bigtext(self, message, text):
        """
        Display a BIGTEXT :D
        Command group: Misc
        Usage: {command_prefix}bigtext [text]
        Example: ~bigtext woohoo
        """
        result = ""
        
        for word in text:
            for s in word:
                if s != ' ':
                    result += ":regional_indicator_%s:" % s
            result += " "

        await message.channel.send(result)

    async def cmd_lenny(self, message, *args):
        '''
        Sends a ( ͡° ͜ʖ ͡°)
        Command group: pics
        Usage: {command_prefix}lenny
        Example: ~lenny
        '''
        await message.channel.send('( ͡° ͜ʖ ͡°)')

    async def cmd_cat(self, message, *args):
        '''
        Sends a random cat from random.cat
        Command group: Misc
        Usage: {command_prefix}cat
        Example: ~cat
        '''
        url = "https://aws.random.cat/meow"
        network_timeout = False

        while not network_timeout:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status == 200:
                        js = await r.json()
                        link = js['path']
                        url = "https://rra.ram.moe%s" % (link)
                        break
                    else:
                        print('Error: %s' % r.status)
                        network_timeout = True
                        return {'error': True, 'message': 'HTTP Error %s. Please try again.' % r.status}

        return {'error': False, 'url': url}

    async def cmd_cardgame(self, message, card_num, *args):
        """
        Play LLSIF card guessing game
        Command group: Games
        Usage:
            {command_prefix}cardgame card_num [diff]
            + card_num: Number of rounds to play
            + diff:
                + easy/e: image size 300x300
                + normal/n: image size 200 x 200
                + hard/h: image size 150 x 150
                + extreme/ex: image size 100 x 100
            Normal diff by default

            stop to stop the game (for who called the game :D)

            Just type the answer without prefix :D
            
            Idol names including: 
                maki, rin, hanayo, kotori, honoka, umi, eli, nozomi, nico,
                ruby, hanamaru, yoshiko, yohane, you, chika, riko, mari, kanan, dia,
                ayumu, ai, setsuna, kanata, karin, emma, rina, shizuku and kasumi,
                and some support characters

            You must answer in 15 seconds :D
        """
        try:
            if self.playing_cardgame:
                await message.channel.send("The game is currently being played. Enjoy!")
                return
        except AttributeError:
            self.playing_cardgame = True

        self.playing_cardgame = True

        diff_size = {
            'easy': 300,
            'normal': 200,
            'hard': 150,
            'extreme': 100,
            'e': 300,
            'n': 200,
            'h': 150,
            'ex': 100
        }
        try:
            card_num = int(card_num)
        except ValueError:
            await message.channel.send("Please type number of rounds correctly")
            self.playing_cardgame = False
            return            

        if not args:
            diff = 'normal'
        else:
            diff = args[0]
            if diff in diff_size:
                pass
            else:
                await message.channel.send("Diff %s not found .-." % diff)
                self.playing_cardgame = False
                return

        user1st = message.author
        userinfo = {user1st.display_name: 0}
        struserlist = ""
        strresult = ""
        
        await message.channel.send("Game starts in 10 seconds. Be ready!")
        checkstart = False
        checktimeout = False
        start = int(time.time())
        logger.info("Game called at %s" % (start))

        def cond(m):
            return m.channel == message.channel

        while True:
            if (int(time.time()) - start >= 10):
                checkstart = True
            try:
                response_message = await self.wait_for('message', check=cond, timeout=10)
            except asyncio.TimeoutError:
                checkstart = True
            else:
                if (response_message.content == 'stop'):
                    await message.channel.send("Game abandoned. Thanks for calling me :D")
                    self.playing_cardgame = False
                    return
            
            if (checkstart == True):
                logger.info("Game starts at %s" % int(time.time()))
                await message.channel.send("Music start!")
                time.sleep(1)
                break

        idol_name = {'eli': 'Ayase Eli', 'rin': 'Hoshizora Rin', 'umi': 'Sonoda Umi', 'hanayo': 'Koizumi Hanayo',
        'honoka': 'Kousaka Honoka', 'kotori': 'Minami Kotori', 'maki': 'Nishikino Maki', 'nozomi': 'Toujou Nozomi', 'nico': 'Yazawa Nico',
        'chika': 'Takami Chika', 'riko': 'Sakurauchi Riko', 'you': 'Watanabe You', 'yoshiko': 'Tsushima Yoshiko', 'yohane': 'Tsushima Yoshiko',
        'ruby': 'Kurosawa Ruby', 'hanamaru': 'Kunikida Hanamaru', 'mari': 'Ohara Mari', 'dia': 'Kurosawa Dia', 'kanan': 'Matsuura Kanan',
        'alpaca': 'Alpaca', 'shiitake': 'Shiitake', 'uchicchi': 'Uchicchi',
        "chika's mother": "Chika's mother", "honoka's mother": "Honoka's mother", "kotori's mother": "Kotori's mother", "maki's mother": "Maki's mother", "nico's mother": "Nico's mother",
        'cocoa': 'Yazawa Cocoa', 'cocoro': 'Yazawa Cocoro', 'cotarou': 'Yazawa Cotarou',
        'ayumu': 'Ayumu Uehara', 'setsuna': 'Setsuna Yuki', 'shizuku': 'Shizuku Osaka', 'karin': 'Karin Asaka', 'kasumi': 'Kasumi Nakasu', 'ai': 'Ai Miyashita', 'rina': 'Rina Tennoji', 'kanata': 'Kanata Konoe', 'emma': 'Emma Verde',
        }
        # posx = [100, 125, 150, 175, 200, 225, 250, 275, 300]
        # posy = [200, 225, 250, 275, 300, 325, 350, 350, 375, 400, 425, 450, 475, 500, 525, 550]
        
        x_range = [100, 512 - diff_size[diff]]
        y_range = [200, 720 - diff_size[diff]]
        card_max = 5000
        found = False
        network_timeout = False
        stop = False
        u1p = 0
        u2p = 0
        dirpath = tempfile.mkdtemp()

        for count in range(0, card_num):
            checktimeout = False

            async with message.channel.typing():
                while (found == False and network_timeout == False):
                    random_num = random.randint(1, card_max)
                    url = 'http://schoolido.lu/api/cards/%s' % (random_num)
                    logger.info('Searched %s' % (url))
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as r:
                            if r.status == 404:
                                card_max = card_max / 2
                                pass
                            elif r.status == 200:
                                js = await r.json()
                                if 'detail' in js:
                                    card_max = card_max / 2
                                else:
                                    selected_idol = js['idol']['name']
                                    if (selected_idol in idol_name.values()):
                                        found = True
                                        img = 'http:%s' % (js['card_image'])
                                        selected_card = js['id']
                                        if img == "http:None":
                                            img = 'http:%s' % (js['card_idolized_image'])
                                        logger.info('Found %s' % (img))
                                        card_max = 5000
                                        break
                                    else:
                                        pass
                            else:
                                logger.info('Network timed out.')
                                network_timeout = True

                found = False
                fd = urllib.request.urlopen(img)
                image_file = io.BytesIO(fd.read())
                im = Image.open(image_file)
                path = "%s/%s.png" % (dirpath, selected_card)
                im.save(path)

                #Crop image and send
                x = random.randint(*x_range)
                y = random.randint(*y_range)
                area = (x, y, x+diff_size[diff], y+diff_size[diff])
                cropped_img = im.crop(area)

                temp_path = "%s/%s_cropped.png" % (dirpath, selected_card)
                cropped_img.save(temp_path)

                await message.channel.send("Question %d of %d. Guess who?" % (count + 1, card_num), file=discord.File(temp_path))

            name_list = ['eli', 'rin', 'hanayo', 'honoka', 'kotori', 'maki', 'umi', 'nozomi', 'nico',
            'chika', 'riko', 'you', 'yoshiko', 'ruby', 'hanamaru', 'mari', 'dia', 'kanan', 'yohane',
            'alpaca', 'shiitake', 'uchicchi',
            "chika's mother", "honoka's mother", "kotori's mother", "maki's mother", "nico's mother",
            'cocoa', 'cocoro', 'cotarou',
            'ayumu', 'ai', 'setsuna', 'kanata', 'karin', 'emma', 'rina', 'shizuku', 'kasumi',
            ]

            start = int(time.time())
            logger.info("Question %d at %s" % (count + 1, int(time.time())))
            strresult = ""
            while True:
                if (int(time.time()) - start) >= 15:
                    checktimeout = True
                try:
                    response_message = await self.wait_for('message', check=cond, timeout=15)
                except asyncio.TimeoutError:
                    response_message = None
                if (checktimeout == True) or (not response_message):
                    logger.info("Time out.")
                    await message.channel.send("Time out! Here's the answer:\n%s, Card No.%s" % (selected_idol, selected_card), file=discord.File(path))
                    break
                answ = response_message.content.lower()
                if (answ in name_list and (idol_name[answ].lower() == selected_idol.lower())):
                    await message.channel.send("10 points for %s\n%s, Card No.%s" % (response_message.author.display_name, selected_idol, selected_card), file=discord.File(path))
                    if response_message.author.display_name not in userinfo:
                        userinfo[response_message.author.display_name] = 0
                    userinfo[response_message.author.display_name] += 10
                    for x in userinfo:
                        strresult += "%s: %s\n" % (x, userinfo[x])
                    await message.channel.send("Round %d result:\n```%s```" % (count + 1, strresult))
                    time.sleep(2)
                    break
                elif (answ == "stop" and response_message.author == user1st):
                    stop = True
                    break
                elif (answ in name_list):
                    await message.channel.send("Try again.")
            
            if stop == True:
                await message.channel.send("Ok. The game stopped!")
                break

            if count + 1 != card_num:
                await message.channel.send("Here comes the next question!")
            time.sleep(1)

        shutil.rmtree(dirpath)

        strresult = ""
        for x in userinfo:
            strresult += "%s: %s\n" % (x, userinfo[x])

        await message.channel.send("Final result:\n```%s```" % (strresult))
        await message.channel.send("Thanks for playing :)))")

        self.playing_cardgame = False

    async def cmd_join(self, message, *args):
        '''
        Join a voice channel
        Command group: Music
        Usage: {command_prefix}join
        Example: ~join
        '''
        try:
            self.voice_channel = message.author.voice.channel
        except AttributeError:
            await message.channel.send('Please join a voice channel first :D')
            return
            
        try:
            self.voice_client = await self.voice_channel.connect()
        except asyncio.TimeoutError:
            await message.channel.send('Could not connect to the voice channel in time')
        except discord.ClientException:
            await message.channel.send('Already connected to voice channel')
        except discord.opus.OpusNotLoaded:
            try:
                from opus_loader import load_opus_lib
                load_opus_lib()
            except RuntimeError:
                await message.channel.send('Error loading opus lib. Cannot join voice channel')
                return

        await message.channel.send('```Connected to "%s"```' % self.voice_channel.name)
    
    async def cmd_leave(self, message, *args):
        '''
        Leave a voice channel
        Command group: Music
        Usage: {command_prefix}leave
        Example: ~leave
        '''
        await self.voice_client.disconnect()
        await message.channel.send('```Left "%s"```' % self.voice_channel.name)
        self.voice_channel = None

    async def cmd_play(self, message, query, *args):
        if not self.voice_channel:
            await self.cmd_join(message)
        
        if query.startswith('https'):
            mode = 'play'
        else:
            mode = 'search'

        try:
            self.music_queue.append(self.process_query(query))
        except 