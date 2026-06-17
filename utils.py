from datetime import datetime
import pytz


def format_datetime(value):

    if not isinstance(
        value,
        datetime
    ):
        value = datetime.fromisoformat(
            str(value)
        )

    ist = pytz.timezone(
        "Asia/Kolkata"
    )

    ist_dt = value.astimezone(
        ist
    )

    return ist_dt.strftime(
        "%d %b %Y at %I:%M %p"
    )