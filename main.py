import discord
import regex as re
import os
from validator import *
import traceback
from db import DB

VALID_BLOCKCHAINS = ['eth', 'sol', 'ada']


class InvalidCommand(Exception):
    """
    An exception to be thrown when an invalid command is encountered
    """

    def __init__(self):
        pass


class WhitelistClient(discord.Client):
    """
    The discord client which manages all guilds and corrosponding data
    """

    def __init__(self, db: DB, *, loop=None, **options):
        """
        Args:
            data (dict): A data dictionary stored in memory.
        """
        super().__init__(loop=loop, **options)
        self.db = db
        self.data = {}
        self.admin_commands = {
            'channel': self.set_whitelist_channel,
            'role': self.set_whitelist_role,
            'blockchain': self.set_blockchain,
            'data': self.get_data,
            'config': self.get_config,
            'clear': self.clear_data,
            'help.admin': self.help_admin
        }
        self.public_commands = {
            'help': self.help,
            'check': self.check
        }
        self.validators = {
            'eth': validate_eth,
            'sol': validate_sol,
            'ada': validate_ada
        }
        self.regex = {
            'channel': re.compile(">channel <#\d+>$"),
            'role': re.compile(">role <@&\d+>$"),
            'blockchain': re.compile(">blockchain \w{3}")
        }

    def _log(self, head: str, text: str) -> None:
        with open('log.txt', 'a+') as log:
            log.write(f"Head: {head}\n   Text: {str(text)}\n\n")

    async def on_ready(self) -> None:
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print("Initialising...")
        async for guild in self.fetch_guilds():
            if self.db.execute('SELECT * FROM discord_server WHERE id=?', (guild.id,)).fetchone() is None:
                print(f"Adding guild '{str(guild)}' to database.")
                self.db.execute(
                    "INSERT INTO discord_server VALUES (?,?,?,?)", (guild.id, None, None, None))
                self.db.commit()
        print("-------------")

    async def set_whitelist_channel(self, message: discord.Message) -> None:
        """ Handles setting the channel that will be used for whitelisting

        Args:
            message (discord.Message): The discord message containing the command request

        Raises:
            InvalidCommand: The message structure was not as expected.
        """
        channels = message.channel_mentions
        if len(channels) != 1 or not self.regex['channel'].fullmatch(message.content):
            raise InvalidCommand()

        self.db.execute("UPDATE discord_server SET whitelist_channel = ? WHERE id = ?",
                        (channels[0].id, message.guild.id))
        self.db.commit()

        await message.reply(f"Successfully set whitelist channel to <#{channels[0].id}>",
                            mention_author=True)

    async def set_whitelist_role(self, message: discord.Message) -> None:
        """ Handles setting the role that will be used for whitelisting

        Args:
            message (discord.Message): The discord message containing the command request

        Raises:
            InvalidCommand: The message structure was not as expected.
        """
        roles = message.role_mentions
        if len(roles) != 1 or not self.regex['role'].fullmatch(message.content):
            raise InvalidCommand()

        self.db.execute("UPDATE discord_server SET whitelist_role = ? WHERE id = ?",
                        (roles[0].id, message.guild.id))
        self.db.commit()

        await message.reply(f"Successfully set whitelist role to <@&{roles[0].id}>",
                            mention_author=True)

    async def set_blockchain(self, message: discord.Message) -> None:
        """ Handles setting the blockchain that will be used for validating wallet addresses.

        Args:
            message (discord.Message): The discord message containing the command request

        Raises:
            InvalidCommand: The message structure was not as expected.
        """
        code = message.content[-3:]
        if code in VALID_BLOCKCHAINS:

            self.db.execute(
                "UPDATE discord_server SET blockchain = ? WHERE id = ?", (code, message.guild.id))
            self.db.commit()

            await message.reply(f"Successfully set blockchain to `{code}`", mention_author=True)
        else:
            raise InvalidCommand()

    async def get_config(self, message: discord.Message) -> None:
        """ Returns the current config of a given server to the user.

        Args:
            message (discord.Message): The discord message that sent the request.
        """
        row = self.db.execute(
            "SELECT * FROM discord_server WHERE id = ?", (message.guild.id,)).fetchone()
        if row is None:
            return
        replyStr = f"""
        Whitelist Channel: {"None" if row["whitelist_channel"] is None else f"<#{row['whitelist_channel']}>"}
        Whitelist Role: {"None" if row["whitelist_role"] is None else f"<@&{row['whitelist_role']}>"}
        Blockchain: {row['blockchain']}
        """
        reply = discord.Embed(
            title=f'Config for {message.guild}', description=replyStr)

        await message.reply(embed=reply, mention_author=True)

    async def get_data(self, message: discord.Message) -> None:
        """ Sends a CSV file to the user containing the current data stored by the bot

        Args:
            message (discord.Message): The discord message that sent the request.
        """
        file_name = f'{message.guild.id}.csv'
        with open(file_name, 'w+') as out_file:
            out_file.write('userId, walletAddress\n')
            out_file.writelines(
                map(lambda t: f"{t['id']},{t['wallet']}\n", self.db.execute("SELECT id, wallet FROM user WHERE discord_server = ?", (message.guild.id,)).fetchall()))
            out_file.flush()
        await message.reply('Data for server is attached.',
                            file=discord.File(file_name))
        os.remove(file_name)

    async def clear_data(self, message: discord.Message) -> None:
        """ Clears the data and config currently stored by the bot regarding the current server

        Args:
            message (discord.Message): The discord message that sent the request.
        """
        self.db.execute(
            "DELETE FROM discord_server WHERE id = ?", (message.guild.id,))
        self.db.execute("INSERT INTO discord_server VALUES (?,?,?,?)",
                        (message.guild.id, None, None, None))
        self.db.commit()
        await message.reply("Server's data has been cleared.")

    async def help_admin(self, message: discord.Message) -> None:
        """ Returns a window that provides some help messages regarding how to use the bot for an admin.

        Args:
            message (discord.Message): The discord message that sent the request.
        """
        msg = discord.Embed(title="Whitelist Manager Help (Admin)")
        desc = "Whitelist Manager is a bot designed to assist you in gathering wallet addresses for NFT drops.\nAfter configuring the discord bot, users who are 'whitelisted' will be able to record their crypto addresses which you can then download as a CSV.\nNote, the `config` must be filled out before the bot will work."
        body = "`>channel #channelName`: Sets the channel to listen for wallet addresses on.\n`>role @roleName`: Sets the role a user must possess to be able to add their address to the whitelist.\n`>blockchain eth/sol/ada`: Select which blockchain this NFT drop will occur on, this allows for validation of the addresses that are added.\n`>config`: View the current server config.\n`>data`: Get discordID:walletAddress pairs in a CSV format.\n`>clear`: Clear the config and data for this server.\n`>help.admin`: This screen.\n`>help`: How to use help screen."
        msg.description = desc
        msg.add_field(name="COMMANDS", value=body)
        await message.reply(embed=msg)

    async def help(self, message: discord.Message) -> None:
        """ Returns a window that provides some help messages regarding how to use the bot.

        Args:
            message (discord.Message): The discord message that sent the request.
        """
        msg = discord.Embed(title="Whitelist Manager Help")
        desc = "Whitelist Manager is a bot designed to assist in gathering wallet addresses for NFT drops."
        body = "`>check`: will tell you whether or not your wallet has been recorded in the whitelist\n`>help`: This screen\n`>help.admin`: Provides a help screen to assist in configuring the bot (admin only).\n\nHow to use: Send your wallet address to the whitelist chat to record it!\nThe message should contain just the wallet address (no `>`)."
        msg.description = desc
        msg.add_field(name="COMMANDS", value=body)
        await message.reply(embed=msg)

    async def check(self, message: discord.Message) -> None:
        row = db.execute("SELECT * FROM user WHERE id = ? AND discord_server = ?",
                         (message.author.id, message.guild.id)).fetchone()
        if row is not None:
            await message.reply(f"You are whitelisted! The last 3 digits of your wallet are: `{row['wallet'][-3:]}`")
        else:
            await message.reply(f"Your wallet is not yet on the whitelist. Use `>help` for more info!.")

    async def on_message(self, message: discord.Message) -> None:
        """ Responds to the 'on_message' event. Runs the appropriate commands given the user has valid privellages.

        Args:
            message (discord.Message): The discord message that sent the request.
        """

        try:
            # we do not want the bot to reply to itself
            if message.author.bot or not isinstance(message.author, discord.member.Member):
                return

            # Handle commands
            if message.author.guild_permissions.administrator and message.content.startswith(">"):
                command = message.content.split()[0][1:]
                if command in self.admin_commands.keys():
                    try:
                        await self.admin_commands[command](message)
                        return
                    except InvalidCommand:
                        await message.reply("Invalid command argument.", mention_author=True)
                    return
                if command in self.public_commands.keys():
                    try:
                        await self.public_commands[command](message)
                        return
                    except InvalidCommand:
                        await message.reply("Invalid command argument.", mention_author=True)
                    return

            # Handle whitelist additions
            server = self.db.execute(
                "SELECT * FROM discord_server WHERE id =?", (message.guild.id,)).fetchone()
            if (message.channel.id == server["whitelist_channel"] and server["whitelist_role"] in map(lambda x: x.id, message.author.roles)):
                if message.content.startswith('>'):
                    command = message.content.split()[0][1:]
                    if command in self.public_commands.keys():
                        try:
                            await self.public_commands[command](message)
                            return
                        except InvalidCommand:
                            await message.reply("Invalid command argument.", mention_author=True)
                    else:
                        commands = str(list(self.public_commands.keys()))[
                            1:-1].replace("'", "`")
                        await message.reply(f'Valid commands are: {commands}, use `>help` for more info.')
                    return

                if server["blockchain"] is None: return

                if self.validators[server["blockchain"]](message.content):
                    db.execute("DELETE FROM user WHERE id = ? and discord_server = ?", (message.author.id, message.guild.id))
                    db.execute("INSERT INTO user (id, discord_server, wallet) VALUES (?, ?, ?)", (message.author.id, message.guild.id, message.content))
                    db.commit()
                    user = message.author
                    try:
                        await user.add_roles(discord.utils.get(user.guild.roles, name="Wallet Verified")) #add the role
                    except Exception as e:
                        print(str(e))
                    await message.reply(
                        f"<@{message.author.id}> your wallet ending in `{message.content[-3:]}` has been validated and recorded.", mention_author=True)
                else:
                    await message.reply(f"The address ending in `{message.content[-3:]}` is invalid.")

                await message.delete()
        except Exception:
            tb = traceback.format_exc()
            exception_string = tb.replace('\n', '---')
            self._log(exception_string,
                      f"{message}\nContent:   {message.content}")

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """ Initialises a server when the bot joins

        Args:
            guild (discord.Guild): The guild that the server has joined

        """
        if db.execute("SELECT * FROM discord_server WHERE id=?", (guild.id,)).fetchone() is None:
            db.execute("INSERT INTO discord_server VALUES (?,?,?,?)", (guild.id, None, None, None))
            db.commit()

        self._log("New Guild", f"{guild.id}, {guild.name}")


if __name__ == '__main__':
    access_token = os.environ["ACCESS_TOKEN"]
    db = DB('data.db')
    client = WhitelistClient(db)
    client.run(access_token)
