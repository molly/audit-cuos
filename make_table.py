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
from dateutil.relativedelta import relativedelta
from datetime import datetime
from constants import COLORS


def make_row(month, userinfo, group):
    row = "| "
    active_this_month = True if "active" not in userinfo else False
    right_removed = False
    right_added = False
    if "active" in userinfo:
        for r in userinfo["active"]:
            if r[0].month <= month <= r[1].month:
                # User was active at some point this month
                active_this_month = True
            if month == r[0].month:
                # Right was added this month
                right_added = True
            if month == r[1].month:
                # Right was removed this month
                right_removed = True

    if userinfo["actions"][month] == 0 and not active_this_month:
        row += "\n"
    else:
        # User was active this month
        row += "{:,}".format(userinfo["actions"][month])
        if right_added:
            row += '<ref name="+{}" />\n'.format(group)
        if right_removed:
            row += '<ref name="-{}" />\n'.format(group)
        if not right_added and not right_removed:
            row += "\n"
    return row


def make_table(users: object, groups: object, months: object, group: object) -> object:
    rows = []
    for user in sorted(users.keys(), key=str.lower):
        userinfo = users[user]
        color = None
        if user in groups["arbs"]:
            color = COLORS["arb"]
        elif user in groups["ombuds"]:
            color = COLORS["ombuds"]
        row = '|- style="background: {}"\n'.format(color) if color else "|-\n"
        row += "| {}\n".format(user)
        for month in months:
            row += make_row(month, userinfo, group)
        rows.append(row)
    rows.append(gather_stats(users, months))
    return "".join(rows)


def gather_stats(users, months):
    totals = {month: 0 for month in months}
    for user in users:
        for month, actions in users[user]["actions"].items():
            totals[month] += actions
    row = "|-\n!Total\n! {:,}\n".format(totals[months[0]])
    for i in range(1, 6):
        this_month = totals[months[i]]
        last_month = totals[months[i - 1]]
        percent_change = (this_month - last_month) / last_month * 100
        color = "red" if percent_change < 0 else "green"
        prefix = "" if percent_change < 0 else "+"
        row += "! {count:,} {{{{fontcolor|{color}|({prefix}{percent_change}%)}}}}\n".format(
            count=totals[months[i]],
            color=color,
            prefix=prefix,
            percent_change=round(percent_change, 1),
        )
    return row


def write_table(*tables):
    file_str = "\n\n\n".join(tables)
    with open("stats.txt", "w+") as f:
        f.write(file_str)
