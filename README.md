# whitelistPy

Whitelist Manager is a discord bot designed to assist you in gathering wallet addresses for NFT drops.
After configuring the discord bot, users who are 'whitelisted' will be able to record their crypto addresses which you can then download as a CSV.
Note, the config must be filled out before the bot will work.

## Invite link
Here is a link to the top.gg page and public instance if you want to use this on your server: [Top.GG](https://top.gg/bot/911822691680526357)

## COMMANDS
Note: you must be administrator to be able to access commands.

**>channel #channelName**: Sets the channel to listen for wallet addresses on.

**>role @roleName**: Sets the role a user must possess to be able to add their address to the whitelist.

**>blockchain eth/sol**: Select which blockchain this NFT drop will occur on, this allows for validation of the addresses that are added.

**>config**: View the current server config.

**>data**: Get discordID:walletAddress pairs in a CSV format.

**>clear**: Clear the config and data for this server.

**>check**: Checks whether your wallet has been recorded in the whitelist.

**>help**: A help screen for users.

**>help.admin**: A help screen for admins.

## USAGE

To run your own instance of this bot:
1. Install python 3.7+
2. `cd` into the directory and run `python -m pip install -r requirements.txt`
3. Set the `ACCESS_TOKEN` environment variable:
    - If you're on linux or mac: `export ACCESS_TOKEN=<your discord application access token here>`
    - If you're on windows: `$Env:ACCESS_TOKEN = "<your discord application access token here>"`
4. `python main.py`
