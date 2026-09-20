import calendar
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo
from croniter import croniter
from schedules.requests import ScheduleConfig


UTC = timezone.utc


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("Datetime must be timezone-aware")
    return dt


def _to_utc(dt: datetime) -> datetime:
    return _ensure_aware(dt).astimezone(UTC)


def _combine_local(
    local_date: date,
    run_time: time,
    timezone_name: str,
) -> datetime:
    tz = ZoneInfo(timezone_name)

    return datetime.combine(
        local_date,
        run_time,
        tzinfo=tz,
    )


def _last_day_of_month(
    year: int,
    month: int,
) -> int:
    return calendar.monthrange(year, month)[1]


def _resolve_day(
    year: int,
    month: int,
    day_of_month: int,
) -> int:
    last_day = _last_day_of_month(year, month)

    if day_of_month == -1:
        return last_day

    # If someone requests 31 in February,
    # use the last valid day of that month.
    return min(day_of_month, last_day)


def _check_end_at(
    candidate: datetime,
    end_at: datetime | None,
) -> datetime | None:
    if end_at is not None and candidate > _to_utc(end_at):
        return None

    return candidate


def _next_once(
    config: ScheduleConfig,
    now: datetime,
) -> datetime | None:
    if config.run_at is None:
        return None

    candidate = _to_utc(config.run_at)

    if candidate < now:
        return None

    return _check_end_at(candidate, config.end_at)


def _next_daily(
    config: ScheduleConfig,
    now: datetime,
) -> datetime | None:
    if config.run_time is None:
        return None

    tz = ZoneInfo(config.timezone)

    start_at = _to_utc(
        config.start_at
        or now
    )

    start_local = start_at.astimezone(tz)
    now_local = now.astimezone(tz)

    candidate_date = max(
        start_local.date(),
        now_local.date(),
    )

    interval = config.interval_count

    days_from_start = (
        candidate_date - start_local.date()
    ).days

    remainder = days_from_start % interval

    if remainder:
        candidate_date += timedelta(
            days=interval - remainder
        )

    candidate = _combine_local(
        candidate_date,
        config.run_time,
        config.timezone,
    )

    candidate_utc = _to_utc(candidate)

    # Candidate may be before start_at because the
    # schedule starts later in the day.
    if candidate_utc < start_at or candidate_utc < now:
        candidate_date += timedelta(days=interval)

        candidate = _combine_local(
            candidate_date,
            config.run_time,
            config.timezone,
        )

        candidate_utc = _to_utc(candidate)

    return _check_end_at(
        candidate_utc,
        config.end_at,
    )


def _next_weekly(
    config: ScheduleConfig,
    now: datetime,
) -> datetime | None:
    if not config.run_time or not config.days_of_week:
        return None

    tz = ZoneInfo(config.timezone)

    start_at = _to_utc(
        config.start_at
        or now
    )

    start_local = start_at.astimezone(tz)
    now_local = now.astimezone(tz)

    start_date = start_local.date()
    current_date = max(
        start_date,
        now_local.date(),
    )

    start_monday = (
        start_date
        - timedelta(days=start_date.weekday())
    )

    interval = config.interval_count

    # Search enough days to find the next valid week.
    search_days = max(
        interval * 7 + 14,
        21,
    )

    allowed_days = set(
        day - 1
        for day in config.days_of_week
    )

    for offset in range(search_days):
        candidate_date = (
            current_date
            + timedelta(days=offset)
        )

        week_start = (
            candidate_date
            - timedelta(days=candidate_date.weekday())
        )

        weeks_since_start = (
            week_start - start_monday
        ).days // 7

        if weeks_since_start < 0:
            continue

        if weeks_since_start % interval != 0:
            continue

        if candidate_date.weekday() not in allowed_days:
            continue

        candidate = _combine_local(
            candidate_date,
            config.run_time,
            config.timezone,
        )

        candidate_utc = _to_utc(candidate)

        if candidate_utc < start_at:
            continue

        if candidate_utc < now:
            continue

        return _check_end_at(
            candidate_utc,
            config.end_at,
        )

    return None


def _add_months(
    year: int,
    month: int,
    months: int,
) -> tuple[int, int]:
    zero_based = (
        year * 12
        + (month - 1)
        + months
    )

    new_year = zero_based // 12
    new_month = zero_based % 12 + 1

    return new_year, new_month


def _next_monthly(
    config: ScheduleConfig,
    now: datetime,
) -> datetime | None:
    if (
        config.run_time is None
        or config.day_of_month is None
    ):
        return None

    tz = ZoneInfo(config.timezone)

    start_at = _to_utc(
        config.start_at
        or now
    )

    start_local = start_at.astimezone(tz)
    now_local = now.astimezone(tz)

    start_year = start_local.year
    start_month = start_local.month

    current_year = now_local.year
    current_month = now_local.month

    months_from_start = (
        (current_year - start_year) * 12
        + (current_month - start_month)
    )

    interval = config.interval_count

    if months_from_start < 0:
        months_from_start = 0

    remainder = months_from_start % interval

    first_offset = months_from_start

    if remainder:
        first_offset += interval - remainder

    for offset in range(
        first_offset,
        first_offset + interval * 3 + 12,
        interval,
    ):
        year, month = _add_months(
            start_year,
            start_month,
            offset,
        )

        day = _resolve_day(
            year,
            month,
            config.day_of_month,
        )

        candidate = _combine_local(
            date(year, month, day),
            config.run_time,
            config.timezone,
        )

        candidate_utc = _to_utc(candidate)

        if candidate_utc < start_at:
            continue

        if candidate_utc < now:
            continue

        return _check_end_at(
            candidate_utc,
            config.end_at,
        )

    return None


def _next_yearly(
    config: ScheduleConfig,
    now: datetime,
) -> datetime | None:
    if (
        config.run_time is None
        or config.day_of_month is None
        or config.month_of_year is None
    ):
        return None

    tz = ZoneInfo(config.timezone)

    start_at = _to_utc(
        config.start_at
        or now
    )

    start_local = start_at.astimezone(tz)
    now_local = now.astimezone(tz)

    start_year = start_local.year
    current_year = max(
        start_year,
        now_local.year,
    )

    years_since_start = (
        current_year - start_year
    )

    interval = config.interval_count

    remainder = years_since_start % interval

    first_offset = years_since_start

    if remainder:
        first_offset += interval - remainder

    for offset in range(
        first_offset,
        first_offset + interval * 5 + 10,
        interval,
    ):
        year = start_year + offset

        month = config.month_of_year

        day = _resolve_day(
            year,
            month,
            config.day_of_month,
        )

        candidate = _combine_local(
            date(year, month, day),
            config.run_time,
            config.timezone,
        )

        candidate_utc = _to_utc(candidate)

        if candidate_utc < start_at:
            continue

        if candidate_utc < now:
            continue

        return _check_end_at(
            candidate_utc,
            config.end_at,
        )

    return None


def _next_specific_dates(
    config: ScheduleConfig,
    now: datetime,
) -> datetime | None:
    if not config.run_time or not config.run_dates:
        return None

    candidates = sorted(
        config.run_dates
    )

    for run_date in candidates:
        candidate = _combine_local(
            run_date,
            config.run_time,
            config.timezone,
        )

        candidate_utc = _to_utc(candidate)

        if candidate_utc < now:
            continue

        if (
            config.start_at is not None
            and candidate_utc < _to_utc(config.start_at)
        ):
            continue

        return _check_end_at(
            candidate_utc,
            config.end_at,
        )

    return None


def _next_cron(
    config: ScheduleConfig,
    now: datetime,
) -> datetime | None:
    if not config.cron_expression:
        return None

    tz = ZoneInfo(config.timezone)

    base = now.astimezone(tz)

    if config.start_at is not None:
        start_local = _to_utc(
            config.start_at
        ).astimezone(tz)

        if start_local > base:
            base = start_local

    cron = croniter(
        config.cron_expression,
        base,
    )

    candidate = cron.get_next(datetime)

    candidate_utc = _to_utc(candidate)

    return _check_end_at(
        candidate_utc,
        config.end_at,
    )


def calculate_next_run_at(
    config: ScheduleConfig,
    *,
    now: datetime | None = None,
) -> datetime | None:
    """
    Calculate the next UTC execution time for a schedule.
    """

    if now is None:
        now = datetime.now(UTC)
    else:
        now = _to_utc(now)

    if config.schedule_type == "ONCE":
        return _next_once(
            config,
            now,
        )

    if config.schedule_type == "DAILY":
        return _next_daily(
            config,
            now,
        )

    if config.schedule_type == "WEEKLY":
        return _next_weekly(
            config,
            now,
        )

    if config.schedule_type == "MONTHLY":
        return _next_monthly(
            config,
            now,
        )

    if config.schedule_type == "YEARLY":
        return _next_yearly(
            config,
            now,
        )

    if config.schedule_type == "SPECIFIC_DATES":
        return _next_specific_dates(
            config,
            now,
        )

    if config.schedule_type == "CRON":
        return _next_cron(
            config,
            now,
        )

    raise ValueError(
        f"Unsupported schedule type: "
        f"{config.schedule_type}"
    )


def prepare_schedule_data(
    config: ScheduleConfig,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """
    Convert the validated Pydantic model into
    database-ready data.
    """

    if now is None:
        now = datetime.now(UTC)
    else:
        now = _to_utc(now)

    start_at = (
        _to_utc(config.start_at)
        if config.start_at is not None
        else now
    )

    next_run_at = calculate_next_run_at(
        config,
        now=now,
    )

    if next_run_at is None:
        raise ValueError(
            "Schedule has no future execution time"
        )

    return {
        "name": config.name,
        "description": config.description,
        "job_type": config.job_type,
        "payload": config.payload,
        "priority": config.priority,
        "max_attempts": config.max_attempts,
        "timeout_seconds": config.timeout_seconds,
        "schedule_type": config.schedule_type,
        "timezone": config.timezone,
        "run_at": (
            _to_utc(config.run_at)
            if config.run_at is not None
            else None
        ),
        "run_time": config.run_time,
        "interval_count": config.interval_count,
        "days_of_week": config.days_of_week,
        "day_of_month": config.day_of_month,
        "month_of_year": config.month_of_year,
        "run_dates": config.run_dates,
        "cron_expression": config.cron_expression,
        "start_at": start_at,
        "end_at": (
            _to_utc(config.end_at)
            if config.end_at is not None
            else None
        ),
        "max_runs": config.max_runs,
        "misfire_policy": config.misfire_policy,
        "next_run_at": next_run_at,
    }