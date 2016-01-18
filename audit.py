# Copyright (c) 2016 Molly White
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
import dateutil.parser
from getpass import getpass
from datetime import datetime, timedelta

USER_AGENT = 'AuditCUOS/0.1, run by {}, https://github.com/molly/audit-cuos'
API_URL = 'https://en.wikipedia.org/w/api.php'


def login():
    """Authenticate and get cookies for later requests."""
    username = input('Username: ')
    password = getpass()
    print("Logging in to account {} on enwiki.".format(username))
    headers = {'user-agent': USER_AGENT}
    params = {'action': 'login', 'format': 'json'}
    payload = {'lgname': username, 'lgpassword': password}
    cookies = ''
    while True:
        r = requests.post(API_URL, params=params, data=payload, headers=headers, cookies=cookies)
        resp = r.json()
        if resp['login']['result'] == 'Success':
            print("Successfully logged in.")
            return r.cookies
        elif resp['login']['result'] == 'NeedToken':
            payload['lgtoken'] = resp['login']['token']
            cookies = r.cookies
        elif resp['login']['result'] == 'Throttled':
            print('Login being throttled. Please wait and try again.')
            return None
        else:
            print('Incorrect username or password.')
            return None


def get_interval():
    """Return a tuple containing 23:59:59 for the last day of the previous month, 00:00:00 for the first day of six
    full months ago, and an array containing the numbers of the months."""
    # Find 23:59:59 for the last day of last month
    end_of_last_month = (datetime.utcnow().replace(day=1) - timedelta(days=1))
    month_ago = datetime(end_of_last_month.year, end_of_last_month.month, end_of_last_month.day, 23, 59, 59)

    # Find 00:00:00 for the first day of six full months ago
    month = (end_of_last_month.month - 5) % 12
    if end_of_last_month.month - 6 < 0:
        year = end_of_last_month.year - 1
    else:
        year = end_of_last_month.year
    six_months_ago = datetime(year, month, 1)

    months = [six_months_ago.month]
    for i in range(5):
        months.append((months[-1]) % 12 + 1)
    return month_ago, six_months_ago, months


def count_checks(params, useragent, cookies, dict_entry):
    """Count how many checks are performed each month for this user."""
    culcontinue = None
    while True:
        if culcontinue:
            params.update({'culcontinue': culcontinue})
        r = requests.get(API_URL, params=params, headers=useragent, cookies=cookies)
        blob = r.json()
        cookies.update(r.cookies)
        checks = blob['query']['checkuserlog']['entries']
        for check in checks:
            dict_entry[dateutil.parser.parse(check['timestamp']).month] += 1
        if 'continue' in blob:
            culcontinue = blob['continue']['culcontinue']
        else:
            return dict_entry, cookies


def count_suppressions(params, useragent, cookies, dict_entry):
    """Count how many suppressions are performed each month for this user."""
    lecontinue = None
    while True:
        if lecontinue:
            params.update({'lecontinue': lecontinue})
        r = requests.get(API_URL, params=params, headers=useragent, cookies=cookies)
        blob = r.json()
        cookies.update(r.cookies)
        suppressions = blob['query']['logevents']
        for suppression in suppressions:
            dict_entry[dateutil.parser.parse(suppression['timestamp']).month] += 1
        if 'continue' in blob:
            lecontinue = blob['continue']['lecontinue']
        else:
            return dict_entry, cookies


def make_table(cu, os, month_ago, six_months_ago, month_array):
    """Create a text file with a table showing checks and suppressions."""
    filename = "{} to {} CUOS Statistics.txt".format(six_months_ago.strftime("%b %Y"), month_ago.strftime("%b %Y"))
    with open(filename, 'w+') as f:
        f.write("Checkuser:\n")
        f.write("User\t{}\n".format("\t".join(map(str, month_array))))
        for user in sorted(cu.keys(), key=str.lower):
            record = cu[user]
            f.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(user, record[month_array[0]], record[month_array[1]],
                                                          record[month_array[2]], record[month_array[3]],
                                                          record[month_array[4]], record[month_array[5]]))
        f.write("\n\n")
        f.write("Oversight:\n")
        f.write("User\t{}\n".format("\t".join(map(str, month_array))))
        for user in sorted(os.keys(), key=str.lower):
            record = os[user]
            f.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(user, record[month_array[0]], record[month_array[1]],
                                                          record[month_array[2]], record[month_array[3]],
                                                          record[month_array[4]], record[month_array[5]]))


def audit():
    """Produce checkuser and oversight counts for all functionaries for the past six (full) months. Does not produce
    results for the current month to date."""
    cookies = login()
    if cookies:
        useragent = {'user-agent': USER_AGENT}
        month_ago, six_months_ago, month_array = get_interval()
        actions_dict = dict.fromkeys(month_array, 0)

        r = requests.get(API_URL,
                         params={'action': 'query', 'list': 'allusers', 'format': 'json',
                                 'augroup': 'checkuser', 'aulimit': '500'},
                         headers=useragent)
        checkusers = r.json()['query']['allusers']
        cookies.update(r.cookies)

        cu_dict = {}
        for cu in checkusers:
            print("Gathering checkuser statistics for {}".format(cu['name']))
            params ={'action': 'query', 'list': 'checkuserlog', 'format': 'json', 'culuser': cu['name'],
                     'cullimit': 500, 'culto': six_months_ago.isoformat(), 'culfrom': month_ago.isoformat()}
            cu_dict[cu['name']], cookies = count_checks(params, useragent, cookies, actions_dict.copy())

        r = requests.get(API_URL,
                         params={'action': 'query', 'list': 'allusers', 'format': 'json',
                                 'augroup': 'oversight', 'aulimit': '500'},
                         headers=useragent)
        oversighters = r.json()['query']['allusers']
        cookies.update(r.cookies)

        os_dict = {}
        for os in oversighters:
            print("Gathering oversight statistics for {}".format(os['name']))
            params={'action': 'query', 'list': 'logevents', 'format': 'json', 'leprop': 'timestamp',
                    'letype': 'suppress', 'leuser': os['name'], 'lelimit': 500, 'leend': six_months_ago.isoformat(),
                    'lestart': month_ago.isoformat()}
            os_dict[os['name']], cookies = count_suppressions(params, useragent, cookies, actions_dict.copy())

        make_table(cu_dict, os_dict, month_ago, six_months_ago, month_array)


if __name__ == '__main__':
    audit()
