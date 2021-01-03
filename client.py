# Copyright (c) 2016-2020 Molly White
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import dateutil.parser
import re
import requests
import pytz
from getpass import getpass
from dateutil.relativedelta import relativedelta
from constants import *

utc = pytz.UTC


def prompt():
    print(
        "Please log in with an English Wikipedia bot password "
        "(https://en.wikipedia.org/wiki/Special:BotPasswords).\nAttempting to log in "
        "with your primary account name and password will not work."
    )
    username = input("Username: ")
    password = getpass()
    return username, password


class Client:
    def __init__(self):
        username, password = prompt()
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT.format(self.username)})

    def _get_userlist_by_userright(self, userright):
        """Get a list of usernames with the specified userright."""
        params = {
            "action": "query",
            "list": "allusers",
            "format": "json",
            "augroup": userright,
            "aulimit": "500",
        }
        r = self.session.get(ENWIKI_API, params=params)
        data = r.json()
        return [u["name"] for u in data["query"]["allusers"]]

    def login(self):
        # Fetch login token
        token_params = {
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json",
        }
        token_r = self.session.get(ENWIKI_API, params=token_params)
        token_data = token_r.json()

        # Log in with bot username, password, and token
        params = {
            "action": "login",
            "lgname": self.username,
            "lgpassword": self.password,
            "lgtoken": token_data["query"]["tokens"]["logintoken"],
            "format": "json",
        }
        login_r = self.session.post(ENWIKI_API, data=params)
        login_data = login_r.json()
        if login_data["login"]["result"] != "Success":
            print(login_data["login"]["result"])
            print(login_data["login"]["reason"])
            return False
        return True

    def get_checkusers(self):
        return self._get_userlist_by_userright("checkuser")

    def get_oversighters(self):
        return self._get_userlist_by_userright("oversight")

    def calculate_ranges(self, events, start_time, end_time):
        active_periods = []
        for ind, event in enumerate(events):
            if event["event"] == "remove":
                if ind == 0:
                    active_periods.append(
                        [
                            (start_time + relativedelta(days=-1)).replace(tzinfo=utc),
                            dateutil.parser.parse(event["timestamp"]),
                        ]
                    )
                else:
                    active_periods.append(
                        [
                            dateutil.parser.parse(events[ind - 1]["timestamp"]),
                            dateutil.parser.parse(event["timestamp"]),
                        ]
                    )
            else:
                if ind == len(events) - 1:
                    # The last event was an "add" event
                    active_periods.append(
                        [
                            dateutil.parser.parse(event["timestamp"]),
                            (end_time + relativedelta(days=+1)).replace(tzinfo=utc),
                        ]
                    )
                else:
                    # This means there was an add event but also a remove event after it,
                    # so it will be handled by the "remove" logic
                    pass
        return active_periods

    def get_former_and_new_cuos(self, start_time, end_time):
        """Find any CU/OS-related userright changes in the past six months so we can
        reflect those changes."""
        addl_cu = {}
        addl_os = {}
        params = {
            "action": "query",
            "list": "logevents",
            "leprop": "title|timestamp|details",
            "letype": "rights",
            "lelimit": "max",
            "lestart": end_time.isoformat(),
            "leend": start_time.isoformat(),
            "format": "json",
        }
        lecontinue = None
        while True:
            if lecontinue:
                params["lecontinue"] = lecontinue
            r = self.session.get(META_API, params=params)
            data = r.json()
            for event in data["query"]["logevents"]:
                if "title" in event and event["title"].endswith("@enwiki"):
                    # Suppressed events won't have a title, so check for that.
                    user = event["title"][5:-7]  # Trim User: prefix and @enwiki suffix
                    oldgroups = event["params"]["oldgroups"]
                    newgroups = event["params"]["newgroups"]
                    if "checkuser" in oldgroups and "checkuser" not in newgroups:
                        # CU removed
                        if user not in addl_cu:
                            addl_cu[user] = []
                        addl_cu[user].insert(
                            0, {"timestamp": event["timestamp"], "event": "remove"}
                        )
                    if "checkuser" not in oldgroups and "checkuser" in newgroups:
                        # CU granted
                        if user not in addl_cu:
                            addl_cu[user] = []
                        addl_cu[user].insert(
                            0, {"timestamp": event["timestamp"], "event": "add"}
                        )
                    if "oversight" in oldgroups and "oversight" not in newgroups:
                        # OS removed
                        if user not in addl_os:
                            addl_os[user] = []
                        addl_os[user].insert(
                            0, {"timestamp": event["timestamp"], "event": "remove"}
                        )
                    if "oversight" not in oldgroups and "oversight" in newgroups:
                        # OS granted
                        if user not in addl_os:
                            addl_os[user] = []
                        addl_os[user].insert(
                            0, {"timestamp": event["timestamp"], "event": "add"}
                        )
            if "continue" in data and "lecontinue" in data["continue"]:
                lecontinue = data["continue"]["lecontinue"]
            else:
                break

        for user in addl_cu.keys():
            addl_cu[user] = self.calculate_ranges(addl_cu[user], start_time, end_time)
        for user in addl_os.keys():
            addl_os[user] = self.calculate_ranges(addl_os[user], start_time, end_time)
        return [addl_cu, addl_os]

    def count_checks(self, cu, month_ago, six_months_ago, months):
        params = {
            "action": "query",
            "list": "checkuserlog",
            "culuser": cu,
            "cullimit": 500,
            "culto": six_months_ago.isoformat(),
            "culfrom": month_ago.isoformat(),
            "format": "json",
        }
        actions = {month.month: 0 for month in months}
        culcontinue = None
        print("Counting checks for {}".format(cu))
        while True:
            if culcontinue:
                params["culcontinue"] = culcontinue
            r = self.session.get(ENWIKI_API, params=params)
            data = r.json()
            for check in data["query"]["checkuserlog"]["entries"]:
                actions[dateutil.parser.parse(check["timestamp"]).month] += 1
            if "continue" in data and "culcontinue" in data["continue"]:
                culcontinue = data["continue"]["culcontinue"]
            else:
                break
        return actions

    def count_suppressions(self, os, month_ago, six_months_ago, months):
        params = {
            "action": "query",
            "list": "logevents",
            "leprop": "timestamp",
            "letype": "suppress",
            "leuser": os,
            "lelimit": 500,
            "leend": six_months_ago.isoformat(),
            "lestart": month_ago.isoformat(),
            "format": "json",
        }
        actions = {month.month: 0 for month in months}
        lecontinue = None
        print("Counting suppressions for {}".format(os))
        while True:
            if lecontinue:
                params["lecontinue"] = lecontinue
            r = self.session.get(ENWIKI_API, params=params)
            data = r.json()
            for supp in data["query"]["logevents"]:
                actions[dateutil.parser.parse(supp["timestamp"]).month] += 1
            if "continue" in data and "lecontinue" in data["continue"]:
                lecontinue = data["continue"]["lecontinue"]
            else:
                break
        return actions

    def get_arbitrators(self):
        params = {
            "action": "parse",
            "format": "json",
            "page": "Wikipedia:Arbitration Committee/Members",
            "prop": "wikitext",
            "formatversion": "2",
        }
        r = self.session.get(ENWIKI_API, params=params)
        data = r.json()
        text = data["parse"]["wikitext"]
        return re.findall(r"\{\{user\|(.*?)\}\}", text)

    def get_ombuds(self):
        params = {
            "action": "query",
            "format": "json",
            "list": "globalallusers",
            "agugroup": "ombuds",
        }
        r = self.session.get(META_API, params=params)
        data = r.json()
        return [u["name"] for u in data["query"]["globalallusers"]]
