from datetime import date


def analyze_delay(
    actual_start,
    actual_end,
    planned_start,
    planned_end,
    status
):
    actual_start = date.fromisoformat(
        str(actual_start).split(" ")[0]
    )

    actual_end = date.fromisoformat(
        str(actual_end).split(" ")[0]
    )

    planned_start = date.fromisoformat(
        str(planned_start).split(" ")[0]
    )

    planned_end = date.fromisoformat(
        str(planned_end).split(" ")[0]
    )

    delay_days = 0

    if actual_end > planned_end:
        delay_days = (actual_end - planned_end).days

    status_lower = status.lower()

    if status_lower == "completed":

        if actual_end < planned_end:
            result_status = "Completed Early"

        elif actual_end == planned_end:
            result_status = "On Time"

        else:
            result_status = "Delayed"

    elif status_lower == "in progress":

        if actual_end > planned_end:
            result_status = "At Risk"

        else:
            result_status = "In Progress"

    else:
        result_status = status

    return {
        "status": result_status,
        "delay_days": delay_days
    }