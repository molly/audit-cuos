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
        "(https://en.wikipedia.org/wiki/Special:BotPasswords).\n Attempting to log in"
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
        token_params = {
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json",
        }
        token_r = self.session.get(url=ENWIKI_API, params=token_params)
        token_data = token_r.json()

        params = {
            "action": "login",
            "lgname": self.username,
            "lgpassword": self.password,
            "lgtoken": token_data["query"]["tokens"]["logintoken"],
            "format": "json",
        }
        login_r = self.session.post(url=ENWIKI_API, data=params)
        login_data = login_r.json()
