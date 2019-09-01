import logging
import subprocess
import os
import bot
import gc

def run():
    try:
        from bot.client import MainClient
        
        client = MainClient()
        client.load_config()
        if not client.prefix:
            print('Prefix is not supported. Please choose a different one')
            exit()
            
        try:
            client.run(client.token)
        except AttributeError:
            if 'BOT_TOKEN' in os.environ:
                client.token = os.environ['BOT_TOKEN']
            else:
                print('No Token specified. Exiting...')
                exit()

        return True

    except ImportError:
        subprocess.call('pip install requirements.txt')
        run()

    except KeyboardInterrupt:
        gc.collect()
        run()

run()