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

import requests
from getpass import getpass
from constants import *
from SECRETS import *


def prompt():
    print(
        "Please log in with an English Wikipedia bot password "
        "(https://en.wikipedia.org/wiki/Special:BotPasswords).\nAttempting to log in"
        "with your primary account name and username will not work."
    )
    return s_username, s_password
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

    def login(self):
        # Fetch login token
        token_params = {
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json",
        }
        token_r = self.session.get(url=ENWIKI_API, params=token_params)
        token_data = token_r.json()

        # Log in with bot username, password, and token
        params = {
            "action": "login",
            "lgname": self.username,
            "lgpassword": self.password,
            "lgtoken": token_data["query"]["tokens"]["logintoken"],
            "format": "json",
        }
        login_r = self.session.post(url=ENWIKI_API, data=params)
        login_data = login_r.json()
        if login_data["login"]["result"] != "Success":
            print(login_data["login"]["result"])
            print(login_data["login"]["reason"])
            return False
        return True

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

    def get_checkusers(self):
        return self._get_userlist_by_userright("checkuser")

    def get_oversighters(self):
        return self._get_userlist_by_userright("oversight")

    def get_former_and_new_cuos(self, end_time, start_time):
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
            "lestart": start_time.isoformat(),
            "leend": end_time.isoformat(),
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
                        # Former CU
                        if user not in addl_cu:
                            addl_cu[user] = {}
                        addl_cu[user]["end"] = event["timestamp"]
                    if "checkuser" not in oldgroups and "checkuser" in newgroups:
                        # New CU
                        if user not in addl_cu:
                            addl_cu[user] = {}
                        addl_cu[user]["start"] = event["timestamp"]
                    if "oversight" in oldgroups and "oversight" not in newgroups:
                        # Former OS
                        if user not in addl_os:
                            addl_os[user] = {}
                        addl_os[user]["end"] = event["timestamp"]
                    if "oversight" not in oldgroups and "oversight" in newgroups:
                        # New OS
                        if user not in addl_os:
                            addl_os[user] = {}
                        addl_os[user]["start"] = event["timestamp"]
            if "continue" in data and "lecontinue" in data["continue"]:
                lecontinue = data["continue"]["lecontinue"]
            else:
                break

        return [addl_cu, addl_os]
