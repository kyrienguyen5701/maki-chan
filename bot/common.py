import discord
import logging

logger = logging.getLogger('Common')

async def delete_message(message):
    try:
        await message.delete()
    except discord.Forbidden:
        logger.error('Delete message failed due to no permission')
        pass

def owner_only(func):
    async def target_func(self, message, *args):
        if str(message.author) == self.owner_id:
            await target_func(message, *args)
        else:
            await message.channel.send('```autohotkey\nSorry. You do not have enough permissions to call this command :D```')

    return target_func