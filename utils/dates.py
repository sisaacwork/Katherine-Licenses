from datetime import date


def ontario_dates() -> tuple[date, date, date]:
    """Returns (renewal_opens, renewal_deadline, today) for the active Ontario CCP year."""
    today = date.today()
    year = today.year
    opens = date(year, 11, 1)
    deadline = date(year, 12, 31)
    if today > deadline:
        year += 1
        opens = date(year, 11, 1)
        deadline = date(year, 12, 31)
    return opens, deadline, today


def illinois_dates() -> tuple[date, date, date]:
    """Returns (cycle_start, deadline, today) for the active Illinois renewal cycle.

    Cycles run Dec 1 (even year) → Nov 30 (odd year): 2025-12-01 to 2027-11-30, etc.
    """
    today = date.today()
    year = 2027
    while date(year, 11, 30) < today:
        year += 2
    deadline = date(year, 11, 30)
    cycle_start = date(year - 2, 12, 1)
    return cycle_start, deadline, today


def days_until(target: date) -> int:
    return (target - date.today()).days


def format_countdown(days: int) -> str:
    if days < 0:
        return f"{abs(days)}d overdue"
    if days == 0:
        return "Today!"
    if days == 1:
        return "Tomorrow"
    if days < 30:
        return f"{days} days"
    months, rem = divmod(days, 30)
    if rem == 0:
        return f"{months} mo"
    return f"{months} mo {rem}d"
