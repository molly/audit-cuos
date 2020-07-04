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

import copy
from client import Client
from datetime import datetime, timedelta


def get_interval():
    """Return a tuple containing 23:59:59 for the last day of the previous month,
    00:00:00 for the first day of six full months ago, and an array containing the
    numbers of the months."""
    # Find 23:59:59 for the last day of last month
    end_of_last_month = datetime.utcnow().replace(day=1) - timedelta(days=1)
    month_ago = datetime(
        end_of_last_month.year,
        end_of_last_month.month,
        end_of_last_month.day,
        23,
        59,
        59,
    )

    # Find 00:00:00 for the first day of six full months ago
    month = (end_of_last_month.month - 6) % 12 + 1
    if month == 0:
        month = 12
    if end_of_last_month.month - 6 < 0:
        year = end_of_last_month.year - 1
    else:
        year = end_of_last_month.year
    six_months_ago = datetime(year, month, 1)

    months = [six_months_ago.month]
    for i in range(5):
        months.append((months[-1]) % 12 + 1)
    return month_ago, six_months_ago, months


def run():
    """Run the audit."""
    client = Client()
    logged_in = client.login()
    if not logged_in:
        return

    month_ago, six_months_ago, months = get_interval()
    empty_user_dict = {
        "start_month": None,
        "end_month": None,
        "actions": dict.fromkeys(months, 0),
    }
    # users_dict = {
    #     "cu": {cu: copy.deepcopy(empty_user_dict) for cu in client.get_checkusers()},
    #     "os": {os: copy.deepcopy(empty_user_dict) for os in client.get_oversighters()},
    # }
    [addl_cu_info, addl_os_info] = client.get_former_and_new_cuos(
        six_months_ago, month_ago
    )


if __name__ == "__main__":
    run()
