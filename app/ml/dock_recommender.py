from typing import List, Dict, Any


def recommend_dock(
    docks: List[Dict[str, Any]],
    truck_eta_hours: float,
    priority: str = "normal",
    load_type: str = "general"
) -> Dict[str, Any]:
    """
    Recommend the most suitable dock for an incoming truck.

    Scoring factors:
    - Dock availability
    - Dock status
    - ETA
    - Priority
    - Load type compatibility
    """

    eligible_docks = []

    for dock in docks:
        status = str(dock.get("status", "")).lower()

        # Only available docks are eligible
        if status != "available":
            continue

        score = 0
        reasons = []

        # --------------------------------------------------
        # Availability score
        # --------------------------------------------------
        score += 50
        reasons.append("Dock is available")

        # --------------------------------------------------
        # Priority handling
        # --------------------------------------------------
        if priority.lower() == "high":
            score += 25
            reasons.append("High priority shipment")

        elif priority.lower() == "medium":
            score += 15
            reasons.append("Medium priority shipment")

        else:
            score += 5
            reasons.append("Normal priority shipment")

        # --------------------------------------------------
        # Load type compatibility
        # --------------------------------------------------
        dock_type = str(dock.get("dock_type", "general")).lower()

        if dock_type == load_type.lower():
            score += 20
            reasons.append("Load type matches dock type")

        elif dock_type == "general":
            score += 10
            reasons.append("General-purpose dock")

        # --------------------------------------------------
        # ETA consideration
        # --------------------------------------------------
        available_in_hours = float(
            dock.get("available_in_hours", 0)
        )

        if available_in_hours <= truck_eta_hours:
            score += 20
            reasons.append("Dock will be available before truck arrival")
        else:
            score -= 20
            reasons.append("Dock may not be available before truck arrival")

        eligible_docks.append(
            {
                "dock_id": dock.get("id"),
                "dock_number": dock.get("dock_number"),
                "yard_name": dock.get("yard_name"),
                "score": score,
                "reasons": reasons
            }
        )

    # ------------------------------------------------------
    # No eligible dock
    # ------------------------------------------------------
    if not eligible_docks:
        return {
            "recommended_dock": None,
            "score": 0,
            "reason": "No eligible dock is currently available",
            "alternatives": []
        }

    # ------------------------------------------------------
    # Rank docks by score
    # ------------------------------------------------------
    eligible_docks.sort(
        key=lambda dock: dock["score"],
        reverse=True
    )

    best_dock = eligible_docks[0]

    return {
        "recommended_dock": best_dock,
        "score": best_dock["score"],
        "reason": "; ".join(best_dock["reasons"]),
        "alternatives": eligible_docks[1:]
    }