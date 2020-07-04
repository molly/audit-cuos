# audit-cuos
Generate activity reports for functionaries on the English Wikipedia.

__Author:__ Molly White<br />
__License:__ [MIT](http://opensource.org/licenses/MIT)<br/>
__Version:__ 0.2<br />

## To use
You will need to have [checkuser](https://en.wikipedia.org/wiki/Wikipedia:CheckUser)
and [oversight](https://en.wikipedia.org/wiki/Wikipedia:Oversight) permissions on the
English Wikipedia to successfully run this script. You will also need to generate a
[bot password](https://en.wikipedia.org/wiki/Special:BotPasswords), which you will use
to log in when prompted. Trying to log in with your main account username and password
will not work.

1. Install with [pip](https://pypi.org/project/pip/): `pip install audit-cuos`
2. When prompted, enter your bot username and password. Make sure you use the bot
    username (e.g., "GorillaWarfare@cuos") and not your main username
    ("GorillaWarfare").
3. The script will output its results to a file called `stats.txt`. Although it does its
    best to find people who have been added/removed from CU/OS groups, it doesn't try to
    determine _why_ someone was added or removed, and so those notations will need to
    be added manually. You should also give the results a once-over to ensure that any
    users who have been renamed are not showing up under both names.
4. Copy the results to the [Audit Statistics](https://en.wikipedia.org/w/index.php?title=Wikipedia:Arbitration_Committee/Audit/Statistics)
    page.