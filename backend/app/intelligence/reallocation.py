def suggest_reallocation(activity, absent_workers, available_workers):
    activity_description = activity.get("activity_description", "")
    discipline = activity.get("discipline", "")

    if not absent_workers:
        return {
            "reallocation_required": False,
            "message": "No worker absence reported."
        }

    suitable_workers = [
        worker for worker in available_workers
        if worker.get("discipline", "").lower() == discipline.lower()
    ]

    if suitable_workers:
        suggested_worker = suitable_workers[0]

        return {
            "reallocation_required": True,
            "activity": activity_description,
            "absent_workers": absent_workers,
            "suggested_worker": suggested_worker,
            "reason": "Worker absence detected. Suitable available worker found."
        }

    return {
        "reallocation_required": True,
        "activity": activity_description,
        "absent_workers": absent_workers,
        "suggested_worker": None,
        "reason": "Worker absence detected, but no suitable available worker was found."
    }