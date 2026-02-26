"""Cron expression to human-readable English translator.

Handles standard 5-field cron expressions, all operators, named values,
and special shorthand strings like @daily.
"""

from __future__ import annotations

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

DOW_NAMES = {
    0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday",
    4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday",
}

MONTH_ABBREVS = {v[:3].upper(): k for k, v in MONTH_NAMES.items()}
DOW_ABBREVS = {v[:3].upper(): k for k, v in DOW_NAMES.items() if k < 7}

SPECIAL_STRINGS: dict[str, str] = {
    "@yearly": "Once a year, at midnight on January 1",
    "@annually": "Once a year, at midnight on January 1",
    "@monthly": "Once a month, at midnight on the 1st",
    "@weekly": "Once a week, at midnight on Sunday",
    "@daily": "Once a day, at midnight",
    "@midnight": "Once a day, at midnight",
    "@hourly": "Once an hour, at minute 0",
    "@reboot": "Once, at system startup",
}


def explain_cron(expression: str) -> str:
    """Convert a cron expression to a human-readable English description."""
    expression = expression.strip()

    if expression.startswith("@"):
        desc = SPECIAL_STRINGS.get(expression.lower())
        if desc:
            return desc
        raise ValueError(f"Unknown special string: {expression}")

    fields = expression.split()
    if len(fields) != 5:
        raise ValueError(
            f"Expected 5 fields (minute hour day-of-month month day-of-week), got {len(fields)}"
        )

    minute, hour, dom, month, dow = fields

    parts: list[str] = []

    # Time description
    time_desc = _describe_time(minute, hour)
    if time_desc:
        parts.append(time_desc)

    # Day-of-month
    dom_desc = _describe_dom(dom)
    if dom_desc:
        parts.append(dom_desc)

    # Month
    month_desc = _describe_month(month)
    if month_desc:
        parts.append(month_desc)

    # Day-of-week
    dow_desc = _describe_dow(dow)
    if dow_desc:
        parts.append(dow_desc)

    return ", ".join(parts) if parts else "Every minute"


def _normalize_named(value: str, mapping: dict[str, int]) -> str:
    """Replace named values (JAN, MON, etc.) with their numeric equivalents."""
    for name, num in mapping.items():
        value = value.upper().replace(name, str(num))
    return value


def _describe_time(minute: str, hour: str) -> str:
    """Describe the minute and hour fields together."""
    min_is_star = minute == "*"
    hour_is_star = hour == "*"

    # Every minute
    if min_is_star and hour_is_star:
        return "Every minute"

    # Step in minutes, every hour: */5 * → "Every 5 minutes"
    if minute.startswith("*/") and hour_is_star:
        step = minute[2:]
        return f"Every {step} minutes"

    # Step in hours: 0 */4 → "At minute 0, every 4 hours"
    if hour.startswith("*/"):
        step = hour[2:]
        min_part = _describe_minute_standalone(minute)
        return f"{min_part}, every {step} hours"

    # Range in hours: * 9-17 → "Every minute, from 9:00 AM through 5:59 PM"
    if min_is_star and "-" in hour and "/" not in hour and "," not in hour:
        lo, hi = hour.split("-", 1)
        return f"Every minute, from {_format_hour(int(lo))} through {_format_hour(int(hi), end=True)}"

    # Step in minute range: 0-30/10 * → "Every 10 minutes from 0 through 30"
    if "/" in minute and "-" in minute.split("/")[0] and hour_is_star:
        range_part, step = minute.split("/", 1)
        lo, hi = range_part.split("-", 1)
        return f"Every {step} minutes, from minute {lo} through {hi}"

    # Range in hours with minute step: */15 9-17
    if minute.startswith("*/") and "-" in hour and "/" not in hour:
        step = minute[2:]
        lo, hi = hour.split("-", 1)
        return (
            f"Every {step} minutes, "
            f"from {_format_hour(int(lo))} through {_format_hour(int(hi), end=True)}"
        )

    # Specific minute, range of hours: 30 9-17
    if minute.isdigit() and "-" in hour and "/" not in hour and "," not in hour:
        lo, hi = hour.split("-", 1)
        return (
            f"At minute {minute}, "
            f"from {_format_hour(int(lo))} through {_format_hour(int(hi), end=True)}"
        )

    # Specific hour, every N minutes
    if minute.startswith("*/") and hour.isdigit():
        step = minute[2:]
        return f"Every {step} minutes, during the {_format_hour(int(hour))} hour"

    # Specific time: 30 2 → "At 02:30 AM"
    if minute.isdigit() and hour.isdigit():
        return f"At {_format_time(int(hour), int(minute))}"

    # Multiple specific hours: 0 9,17
    if minute.isdigit() and "," in hour:
        hours = [int(h) for h in hour.split(",")]
        hour_strs = [_format_time(h, int(minute)) for h in hours]
        return f"At {_join_list(hour_strs)}"

    # Every minute during specific hour
    if min_is_star and hour.isdigit():
        return f"Every minute, during the {_format_hour(int(hour))} hour"

    # Multiple specific minutes
    if "," in minute and hour_is_star:
        mins = minute.split(",")
        return f"At minutes {_join_list(mins)}"

    if "," in minute and hour.isdigit():
        mins = minute.split(",")
        return f"At minutes {_join_list(mins)}, during the {_format_hour(int(hour))} hour"

    # Fallback: describe each independently
    parts = []
    min_desc = _describe_minute_standalone(minute)
    if min_desc:
        parts.append(min_desc)
    hour_desc = _describe_hour_standalone(hour)
    if hour_desc:
        parts.append(hour_desc)
    return ", ".join(parts) if parts else "Every minute"


def _describe_minute_standalone(minute: str) -> str:
    if minute == "*":
        return "Every minute"
    if minute.startswith("*/"):
        return f"Every {minute[2:]} minutes"
    if minute.isdigit():
        return f"At minute {minute}"
    if "," in minute:
        return f"At minutes {_join_list(minute.split(','))}"
    if "-" in minute:
        lo, hi = minute.split("-", 1)
        return f"From minute {lo} through {hi}"
    return f"At minute {minute}"


def _describe_hour_standalone(hour: str) -> str:
    if hour == "*":
        return ""
    if hour.startswith("*/"):
        return f"every {hour[2:]} hours"
    if hour.isdigit():
        return f"at {_format_hour(int(hour))}"
    if "-" in hour:
        lo, hi = hour.split("-", 1)
        return f"from {_format_hour(int(lo))} through {_format_hour(int(hi), end=True)}"
    if "," in hour:
        hours = [_format_hour(int(h)) for h in hour.split(",")]
        return f"at {_join_list(hours)}"
    return f"at hour {hour}"


def _describe_dom(dom: str) -> str:
    if dom == "*":
        return ""
    if dom.startswith("*/"):
        return f"every {dom[2:]} days"
    if dom.isdigit():
        return f"on day {dom} of the month"
    if "," in dom:
        return f"on days {_join_list(dom.split(','))} of the month"
    if "-" in dom:
        lo, hi = dom.split("-", 1)
        return f"on days {lo} through {hi} of the month"
    return f"on day {dom} of the month"


def _describe_month(month: str) -> str:
    month = _normalize_named(month, MONTH_ABBREVS)
    if month == "*":
        return ""
    if month.isdigit():
        name = MONTH_NAMES.get(int(month), f"month {month}")
        return f"in {name}"
    if "," in month:
        names = [MONTH_NAMES.get(int(m), f"month {m}") for m in month.split(",")]
        return f"in {_join_list(names)}"
    if "-" in month:
        lo, hi = month.split("-", 1)
        lo_name = MONTH_NAMES.get(int(lo), f"month {lo}")
        hi_name = MONTH_NAMES.get(int(hi), f"month {hi}")
        return f"from {lo_name} through {hi_name}"
    return f"in month {month}"


def _describe_dow(dow: str) -> str:
    dow = _normalize_named(dow, DOW_ABBREVS)
    if dow == "*":
        return ""
    if dow.isdigit():
        name = DOW_NAMES.get(int(dow), f"day {dow}")
        return f"on {name}"
    if "," in dow:
        names = [DOW_NAMES.get(int(d), f"day {d}") for d in dow.split(",")]
        return f"on {_join_list(names)}"
    if "-" in dow:
        lo, hi = dow.split("-", 1)
        lo_name = DOW_NAMES.get(int(lo), f"day {lo}")
        hi_name = DOW_NAMES.get(int(hi), f"day {hi}")
        return f"{lo_name} through {hi_name}"
    return f"on day-of-week {dow}"


def _format_time(hour: int, minute: int) -> str:
    """Format hour and minute as 12-hour time like '02:30 AM'."""
    period = "AM" if hour < 12 else "PM"
    display_hour = hour % 12
    if display_hour == 0:
        display_hour = 12
    return f"{display_hour:02d}:{minute:02d} {period}"


def _format_hour(hour: int, *, end: bool = False) -> str:
    """Format an hour value. If end=True, shows the last minute of that hour."""
    period = "AM" if hour < 12 else "PM"
    display_hour = hour % 12
    if display_hour == 0:
        display_hour = 12
    if end:
        return f"{display_hour}:59 {period}"
    return f"{display_hour}:00 {period}"


def _join_list(items: list[str]) -> str:
    """Join items with commas and 'and' for the last item."""
    if len(items) <= 1:
        return items[0] if items else ""
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def validate_cron(expression: str) -> tuple[bool, str]:
    """Validate a cron expression and return (is_valid, message).

    Returns a tuple of (True, "Valid cron expression") or
    (False, "<specific error message>").
    """
    expression = expression.strip()

    if expression.startswith("@"):
        if expression.lower() in SPECIAL_STRINGS:
            return True, f"Valid special string: {expression}"
        return False, f"Unknown special string: {expression}"

    fields = expression.split()
    if len(fields) != 5:
        return False, (
            f"Expected 5 fields (minute hour day-of-month month day-of-week), "
            f"got {len(fields)}"
        )

    field_names = ["minute", "hour", "day-of-month", "month", "day-of-week"]
    field_ranges = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]
    named_maps = [None, None, None, MONTH_ABBREVS, DOW_ABBREVS]

    for i, (field, name, (lo, hi), named) in enumerate(
        zip(fields, field_names, field_ranges, named_maps)
    ):
        normalized = field
        if named:
            normalized = _normalize_named(field, named)

        ok, msg = _validate_field(normalized, name, lo, hi)
        if not ok:
            return False, msg

    return True, "Valid cron expression"


def _validate_field(
    field: str, name: str, range_lo: int, range_hi: int
) -> tuple[bool, str]:
    """Validate a single cron field."""
    # Handle comma-separated lists
    for part in field.split(","):
        ok, msg = _validate_part(part, name, range_lo, range_hi)
        if not ok:
            return False, msg
    return True, ""


def _validate_part(
    part: str, name: str, range_lo: int, range_hi: int
) -> tuple[bool, str]:
    """Validate a single component of a cron field (handles *, ranges, steps)."""
    # Handle step values
    if "/" in part:
        base, step_str = part.split("/", 1)
        if not step_str.isdigit() or int(step_str) == 0:
            return False, f"Invalid step value '{step_str}' in {name} field"
        # Validate the base part (without the step)
        if base == "*":
            return True, ""
        return _validate_range_or_value(base, name, range_lo, range_hi)

    return _validate_range_or_value(part, name, range_lo, range_hi)


def _validate_range_or_value(
    part: str, name: str, range_lo: int, range_hi: int
) -> tuple[bool, str]:
    """Validate a range (N-M) or single value."""
    if part == "*":
        return True, ""

    if "-" in part:
        pieces = part.split("-", 1)
        for p in pieces:
            if not p.isdigit():
                return False, f"Invalid value '{p}' in {name} field"
            val = int(p)
            if val < range_lo or val > range_hi:
                return False, (
                    f"Value {val} out of range ({range_lo}-{range_hi}) "
                    f"in {name} field"
                )
        return True, ""

    if not part.isdigit():
        return False, f"Invalid value '{part}' in {name} field"

    val = int(part)
    if val < range_lo or val > range_hi:
        return False, (
            f"Value {val} out of range ({range_lo}-{range_hi}) in {name} field"
        )
    return True, ""
