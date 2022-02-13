"""
This script makes the bot leave servers who have not yet used it.

The bot is currently limited to 100 servers by discord so this helps keep it in healthy servers.
"""

import discord
import os
from db import DB

class WhitelistClient(discord.Client):
    def __init__(self, db: DB, *, loop=None, **options):
        """
        Args:
            data (dict): A data dictionary stored in memory.
        """
        super().__init__(loop=loop, **options)
        self.db = db

    async def on_ready(self) -> None:
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print("Removing dead servers...")
        bad_servers = self.db.execute('SELECT id FROM discord_server as ds WHERE NOT EXISTS (SELECT * FROM user WHERE discord_server = ds.id)').fetchall()
        bad_servers = [server['id'] for server in bad_servers]

        async for guild in self.fetch_guilds():
            if guild.id in bad_servers:
                print(f"Leaving {str(guild)}.")
                await guild.leave()
        print("-------------")
        await self.close()


if __name__ == '__main__':
    access_token = os.environ["ACCESS_TOKEN"]
    db = DB('data.db')
    client = WhitelistClient(db)
    client.run(access_token)