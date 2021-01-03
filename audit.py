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

from client import Client
from datetime import datetime, timedelta
from dateutil.relativedelta import *
from make_table import make_table, write_table
import pytz

utc = pytz.UTC


def get_interval():
    """Return a tuple containing 23:59:59 for the last day of the previous month,
    00:00:00 for the first day of six full months ago, and an array containing the
    numbers of the months."""
    # Find 23:59:59 for the last day of last month
    end_of_last_month = datetime.now(tz=utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(microseconds=1)

    # Find 00:00:00 for the first day of six full months ago
    month_ago = datetime(end_of_last_month.year, end_of_last_month.month, 1)

    six_months_ago = month_ago - relativedelta(months=5)

    months = [six_months_ago]
    for i in range(5):
        months.append(six_months_ago + relativedelta(months=i + 1))

    return end_of_last_month, six_months_ago, months


def run():
    """Run the audit."""
    client = Client()
    logged_in = client.login()
    if not logged_in:
        return

    interval_data = get_interval()
    month_ago, six_months_ago, months = interval_data

    # Gather lists of current, former, and new CU/OS
    users_dict = {
        "cu": {cu: {} for cu in client.get_checkusers()},
        "os": {os: {} for os in client.get_oversighters()},
    }
    [addl_cu_info, addl_os_info] = client.get_former_and_new_cuos(
        six_months_ago, month_ago
    )

    # Merge data about current, former, and new CU/OS
    for cu, info in addl_cu_info.items():
        if cu not in users_dict["cu"]:
            users_dict["cu"][cu] = {}
        users_dict["cu"][cu].update({"active": info})
    for os, info in addl_os_info.items():
        if os not in users_dict["os"]:
            users_dict["os"][os] = {}
        users_dict["os"][os].update({"active": info})

    # Gather statistics
    for cu in users_dict["cu"]:
        actions = client.count_checks(cu, *interval_data)
        users_dict["cu"][cu]["actions"] = actions
    for os in users_dict["os"]:
        actions = client.count_suppressions(os, *interval_data)
        users_dict["os"][os]["actions"] = actions

    # Get members of groups that are exempt from activity requirements so we can mark
    # that in the table
    groups = {"arbs": client.get_arbitrators(), "ombuds": client.get_ombuds()}

    # Create the wikitext table from the data we've gathered
    cu_table = make_table(users_dict["cu"], groups, months, "cu")
    os_table = make_table(users_dict["os"], groups, months, "os")

    # Write to file
    write_table(cu_table, os_table)


if __name__ == "__main__":
    run()
