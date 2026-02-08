"""
PactLens Risk Analysis Utilities
Risk heatmap generation and scoring
"""

from typing import List, Dict, Any


def generate_risk_heatmap(contradictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a clause risk heatmap from contradictions.
    
    Groups contradictions by clause_type and aggregates risk levels.
    
    Args:
        contradictions: List of contradiction dicts with:
            - clause_type_display: str (e.g., "Confidentiality")
            - risk_level: str ("high", "medium", "low")
    
    Returns:
        Dict with:
        - heatmap: List of risk summaries per clause type (sorted by risk_score desc)
        - top_risky_category: str or None
    
    Example:
        >>> contradictions = [
        ...     {"clause_type_display": "Confidentiality", "risk_level": "high"},
        ...     {"clause_type_display": "Confidentiality", "risk_level": "medium"},
        ...     {"clause_type_display": "Compensation", "risk_level": "low"}
        ... ]
        >>> result = generate_risk_heatmap(contradictions)
        >>> result["top_risky_category"]
        "Confidentiality"
    """
    
    if not contradictions:
        return {
            "heatmap": [],
            "top_risky_category": None
        }
    
    # Group by clause_type
    risk_groups: Dict[str, Dict[str, int]] = {}
    
    for contradiction in contradictions:
        clause_type = contradiction.get("clause_type_display", "General")
        risk_level = contradiction.get("risk_level", "low").lower()
        
        if clause_type not in risk_groups:
            risk_groups[clause_type] = {"high": 0, "medium": 0, "low": 0}
        
        if risk_level in risk_groups[clause_type]:
            risk_groups[clause_type][risk_level] += 1
    
    # Compute heatmap
    heatmap = []
    
    for clause_type, risks in risk_groups.items():
        high = risks.get("high", 0)
        medium = risks.get("medium", 0)
        low = risks.get("low", 0)
        
        # Risk score: high=3, medium=2, low=1
        risk_score = (high * 3) + (medium * 2) + (low * 1)
        
        # Heat level assignment
        if risk_score >= 6:
            heat_level = "high"
        elif 3 <= risk_score <= 5:
            heat_level = "medium"
        else:
            heat_level = "low"
        
        heatmap.append({
            "clause_type": clause_type,
            "high": high,
            "medium": medium,
            "low": low,
            "risk_score": risk_score,
            "heat_level": heat_level,
            "conflict_count": high + medium + low
        })
    
    # Sort by risk_score descending
    heatmap.sort(key=lambda x: x["risk_score"], reverse=True)
    
    # Get top risky category
    top_risky_category = heatmap[0]["clause_type"] if heatmap else None
    
    return {
        "heatmap": heatmap,
        "top_risky_category": top_risky_category
    }


def compute_overall_risk(heatmap: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute overall contract risk based on heatmap.
    
    Args:
        heatmap: List of risk summaries from generate_risk_heatmap
    
    Returns:
        Dict with:
        - overall_score: float (0-10)
        - overall_level: str ("high", "medium", "low")
        - summary: str
    """
    
    if not heatmap:
        return {
            "overall_score": 0.0,
            "overall_level": "low",
            "summary": "No risks detected."
        }
    
    # Calculate average risk per conflict
    total_score = sum(h["risk_score"] for h in heatmap)
    total_conflicts = sum(h["conflict_count"] for h in heatmap)
    
    # Normalize to 0-10 scale based on average conflict weight
    # Max per conflict: 3 (high) → average max = 3
    if total_conflicts > 0:
        average_weight = total_score / total_conflicts
        # Scale: 0 = 0/10, 1.5 = 5/10, 3.0 = 10/10
        normalized_score = min(10.0, (average_weight / 3.0) * 10.0)
    else:
        normalized_score = 0.0
    
    # Determine overall level
    if normalized_score >= 7.0:
        overall_level = "high"
        summary = f"Significant risks detected across {total_conflicts} conflicts. Review recommended."
    elif normalized_score >= 4.0:
        overall_level = "medium"
        summary = f"Moderate risks detected across {total_conflicts} conflicts. Consider review."
    else:
        overall_level = "low"
        summary = f"Minor risks detected across {total_conflicts} conflicts."
    
    return {
        "overall_score": round(normalized_score, 1),
        "overall_level": overall_level,
        "summary": summary
    }
