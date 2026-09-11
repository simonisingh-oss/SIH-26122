import json


# Construction activity dependencies
# Key = activity
# Value = activity that depends on it
DEPENDENCIES = {
    "PIP-3100-0110": [
        ("PIP-3100-0120", "Erect Line - Suction Header Rack Section 3")
    ],

    "PIP-3100-0120": [
        ("PIP-3100-0130", "Weld Joints - Suction Header Rack Section 3")
    ],

    "PIP-3100-0130": [
        ("PIP-3100-0140", "Hydrotest - Suction Header Line")
    ],

    "CIV-2200-0030": [
        ("CIV-2200-0040", "Pour Concrete - Foundation Grid A1-A4")
    ],

    "CIV-2200-0040": [
        ("CIV-2200-0050", "Backfill & Compaction - Foundation Grid A1-A4")
    ],
}


def analyze_activity(activity):
    """
    Detect problems in an activity.
    """

    insights = []

    status = activity.get("status", "Unknown")
    percent = activity.get("percent_complete")
    delay_reason = activity.get("delay_reason")
    activity_name = activity.get("activity_description", "Unknown activity")
    activity_id = activity.get("matched_activity_id")

    # Delay detection
    if status == "Delayed":
        insights.append({
            "type": "Delay Alert",
            "severity": "High",
            "message": f"{activity_name} is delayed.",
            "reason": delay_reason
        })

    # Low progress detection
    if percent is not None:
        if percent < 50 and status == "In Progress":
            insights.append({
                "type": "Low Progress Alert",
                "severity": "Medium",
                "message": f"{activity_name} is only {percent}% complete.",
                "action": "Monitor closely and check for execution blockers."
            })

    # Downstream impact detection
    if activity_id in DEPENDENCIES:

        affected_activities = DEPENDENCIES[activity_id]

        if status == "Delayed" or (
            percent is not None and percent < 50
        ):
            for affected_id, affected_name in affected_activities:

                insights.append({
                    "type": "Downstream Impact",
                    "severity": "High",
                    "message": (
                        f"{activity_name} may affect downstream activity "
                        f"{affected_name}."
                    ),
                    "affected_activity_id": affected_id,
                    "affected_activity_name": affected_name,
                    "action": (
                        "Prioritize the current activity or resolve "
                        "the blocker."
                    )
                })

    return insights

def calculate_risk_score(status, percent, impact_level, dependency_depth):
    """
    Calculate a risk score from execution status and downstream impact.
    Score range: 0-100.
    """

    score = 0

    # Execution status
    if status == "Delayed":
        score += 50
    elif status == "In Progress":
        score += 20

    # Progress level
    if percent is not None:
        if percent < 25:
            score += 30
        elif percent < 50:
            score += 20
        elif percent < 75:
            score += 10

    # Direct impact is more immediate
    if impact_level == "Direct":
        score += 15
    else:
        score += 5

    # Deeper dependency = greater uncertainty / propagation
    score += min(dependency_depth * 5, 10)

    return min(score, 100)

def generate_recommended_action(activity_name, status, delay_reason):
    """
    Generate a specific recommended action based on the
    execution status and reported delay reason.
    """

    if status != "Delayed":
        return (
            f"Prioritize '{activity_name}' to prevent "
            f"downstream delay."
        )

    if not delay_reason:
        return (
            f"Investigate the blocker affecting '{activity_name}' "
            f"and prioritize resolution."
        )

    reason = delay_reason.lower()

    if "welder" in reason or "welding" in reason:
        return (
            f"Arrange or reassign an available qualified welder "
            f"for '{activity_name}'."
        )

    if "material" in reason or "delivery" in reason:
        return (
            f"Expedite material delivery and verify material "
            f"availability for '{activity_name}'."
        )

    if "equipment" in reason or "machine" in reason:
        return (
            f"Arrange alternative equipment or resolve the "
            f"equipment issue affecting '{activity_name}'."
        )

    if "manpower" in reason or "worker" in reason or "labour" in reason:
        return (
            f"Reallocate additional manpower to '{activity_name}' "
            f"to recover progress."
        )

    if "weather" in reason or "rain" in reason:
        return (
            f"Reschedule affected work and prioritize activities "
            f"that can continue despite the weather constraint."
        )

    if "approval" in reason or "permit" in reason:
        return (
            f"Expedite the required approval or permit for "
            f"'{activity_name}'."
        )

    return (
        f"Investigate and resolve the reported blocker "
        f"('{delay_reason}') affecting '{activity_name}'."
    )

def predict_risks(activities):
    """
    Predict risks through the complete downstream dependency chain.

    Handles:
    - Direct downstream impact
    - Indirect downstream impact
    - Multiple downstream branches
    - Completed-activity filtering
    - Duplicate-risk prevention
    """

    risks = []

    # Store reported activity information by schedule ID
    activity_status = {}

    for activity in activities:
        activity_id = activity.get("matched_activity_id")

        if activity_id:
            activity_status[activity_id] = activity

    # Keep track of risks already reported
    reported_risks = set()

    # Check every reported activity
    for activity in activities:

        activity_id = activity.get("matched_activity_id")
        activity_name = activity.get(
            "activity_description",
            "Unknown activity"
        )

        status = activity.get("status", "Unknown")
        percent = activity.get("percent_complete")

        # Determine whether the current activity is at risk
        predecessor_at_risk = (
            status == "Delayed"
            or (percent is not None and percent < 50)
        )

        if not predecessor_at_risk:
            continue

        # Queue for breadth-first dependency traversal
        queue = [(activity_id, 0)]
        visited = set()

        while queue:

            current_id, depth = queue.pop(0)

            # Prevent cycles
            if current_id in visited:
                continue

            visited.add(current_id)

            if current_id not in DEPENDENCIES:
                continue

            for downstream_id, downstream_name in DEPENDENCIES[current_id]:

                # Do not report an already completed activity
                downstream_activity = activity_status.get(downstream_id)

                if downstream_activity:
                    downstream_status = downstream_activity.get(
                        "status",
                        "Unknown"
                    )

                    if downstream_status == "Completed":
                        continue

                # Direct = first dependency level
                # Indirect = further downstream
                impact_level = (
                    "Direct"
                    if depth == 0
                    else "Indirect"
                )

                # Calculate intelligent risk score
                risk_score = calculate_risk_score(
                    status,
                    percent,
                    impact_level,
                    depth
                )

                # Convert score into severity
                if risk_score >= 70:
                    severity = "Critical"
                elif risk_score >= 50:
                    severity = "High"
                elif risk_score >= 30:
                    severity = "Medium"
                else:
                    severity = "Low"

                # Build reason and recommended action
                if status == "Delayed":
                    reason = (
                        f"Predecessor '{activity_name}' is delayed."
                    )
                else:
                    reason = (
                        f"Predecessor '{activity_name}' is only "
                        f"{percent}% complete."
                    )

                recommended_action = generate_recommended_action(
                    activity_name,
                    status,
                    activity.get("delay_reason")
                )
                    
                # Prevent duplicate risk entries
                risk_key = (
                    activity_id,
                    downstream_id,
                    impact_level
                )

                if risk_key in reported_risks:
                    continue

                reported_risks.add(risk_key)

                risks.append({
                    "type": "Predicted Risk",
                    "severity": severity,
                    "risk_score": risk_score,
                    "impact_level": impact_level,
                    "at_risk_activity_id": downstream_id,
                    "at_risk_activity": downstream_name,
                    "reason": reason,
                    "recommended_action": recommended_action
                })

                # Continue through the dependency chain
                queue.append(
                    (downstream_id, depth + 1)
                )

    return risks

def generate_execution_summary(activities):

    summary = {
        "total_activities": len(activities),
        "completed": 0,
        "in_progress": 0,
        "delayed": 0,
        "alerts": []
    }

    for activity in activities:

        status = activity.get("status", "Unknown")

        if status == "Completed":
            summary["completed"] += 1

        elif status == "In Progress":
            summary["in_progress"] += 1

        elif status == "Delayed":
            summary["delayed"] += 1

        insights = analyze_activity(activity)

        summary["alerts"].extend(insights)

    return summary


if __name__ == "__main__":

    print("Proactive Execution Intelligence")
    print("--------------------------------\n")

    # Sample activities
    activities = [

        {
            "activity_description": "Fabricate Spool",
            "matched_activity_id": "PIP-3100-0110",
            "status": "Completed",
            "percent_complete": 100,
            "delay_reason": None
        },

        {
            "activity_description": "Erect Line - Suction Header Rack Section 3",
            "matched_activity_id": "PIP-3100-0120",
            "status": "In Progress",
            "percent_complete": 40,
            "delay_reason": None
        },

        {
            "activity_description": "Weld Joints - Suction Header Rack Section 3",
            "matched_activity_id": "PIP-3100-0130",
            "status": "Delayed",
            "percent_complete": 60,
            "delay_reason": "Welder unavailable"
        }
    ]

    result = generate_execution_summary(activities)

    result["predicted_risks"] = predict_risks(activities)

    print(json.dumps(result, indent=2))