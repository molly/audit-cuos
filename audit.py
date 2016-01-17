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

from mwclient import Site
from getpass import getpass
from datetime import datetime, timedelta

USER_AGENT = 'AuditCUOS/0.1, run by {}, https://github.com/molly/audit-cuos'
API = 'en.wikipedia.org/w/api.php'
TIMESTAMP_FORMAT = '%H:%M, %d %B %Y'


def audit():
    """Produce checkuser and oversight counts for all functionaries for the past six (full) months. Does not produce
    results for the current month to date."""
    username = input('Username: ')
    password = #getpass()
    month_ago, six_months_ago, month_array = get_interval()

    site = Site('en.wikipedia.org', clients_useragent=USER_AGENT.format(username))
    site.login(username, password)

    checkusers = site.allusers(group='checkuser')
    oversighters = site.allusers(group='oversight')

    cu_dict = {}
    for cu in checkusers:
        cu_dict[cu['name']] = {}
        checks = site.logevents('checkuserlog', user=cu['name'], limit=1)
        for check in checks:
            print(check)
        break

    # os_dict = {}
    # for os in oversighters:
    #     os_dict[os['name']] = dict.fromkeys(month_array, 0)
    #     suppressions = site.logevents('suppress', user=os['name'], start=month_ago.isoformat(),
    #                                   end=six_months_ago.isoformat())
    #     for s in suppressions:
    #         os_dict[os['name']][s['timestamp'][1]] += 1


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


if __name__ == '__main__':
    audit()