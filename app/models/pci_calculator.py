# app/models/pci_calculator.py
from typing import List, Dict

def calculate_pci_score(detections: List[Dict]) -> Dict:
    """Calculate PCI score for YOUR custom defect types"""
    
    if not detections:
        return {
            'pci_score': 100,
            'condition': 'Excellent',
            'total_deduct': 0,
            'deduct_breakdown': {}
        }
    
    total_deduct = 0
    deduct_breakdown = {}
    
    # YOUR CUSTOM DEDUCT VALUES
    deduct_values = {
        'apothole': {'low': 15, 'medium': 25, 'high': 40, 'critical': 60},
        'spalling': {'low': 10, 'medium': 20, 'high': 35, 'critical': 50},
        'patching': {'low': 3, 'medium': 5, 'high': 10, 'critical': 15},
        'rm': {'low': 8, 'medium': 15, 'high': 25, 'critical': 40}
    }
    
    for detection in detections:
        defect_type = detection['type']
        severity = detection['severity']
        
        if defect_type in deduct_values:
            deduct = deduct_values[defect_type].get(severity, 5)
        else:
            deduct = {'low': 5, 'medium': 10, 'high': 20, 'critical': 30}.get(severity, 10)
        
        total_deduct += deduct
        
        key = f"{defect_type}_{severity}"
        deduct_breakdown[key] = deduct_breakdown.get(key, 0) + deduct
    
    # Density adjustment
    defect_count = len(detections)
    if defect_count > 10:
        density_penalty = min((defect_count - 10) * 2, 20)
        total_deduct += density_penalty
        deduct_breakdown['density_penalty'] = density_penalty
    
    total_deduct = min(total_deduct, 100)
    pci_score = max(0, 100 - total_deduct)
    
    condition = get_condition_rating(pci_score)
    
    return {
        'pci_score': round(pci_score, 1),
        'condition': condition,
        'total_deduct': round(total_deduct, 1),
        'deduct_breakdown': deduct_breakdown,
        'defect_count': defect_count
    }

def get_condition_rating(pci_score: float) -> str:
    """Get condition rating from PCI score"""
    if pci_score >= 85:
        return 'Excellent'
    elif pci_score >= 70:
        return 'Very Good'
    elif pci_score >= 55:
        return 'Good'
    elif pci_score >= 40:
        return 'Fair'
    elif pci_score >= 25:
        return 'Poor'
    elif pci_score >= 10:
        return 'Very Poor'
    else:
        return 'Failed'

def generate_recommendations(pci_score: float, detections: List[Dict]) -> List[str]:
    """Generate recommendations for YOUR defect types"""
    recommendations = []
    
    if pci_score >= 85:
        recommendations.append("Routine maintenance recommended - pavement in excellent condition")
    elif pci_score >= 70:
        recommendations.append("Preventive maintenance within 12 months recommended")
    elif pci_score >= 55:
        recommendations.append("Corrective maintenance within 6 months recommended")
    elif pci_score >= 40:
        recommendations.append("Major rehabilitation within 3 months required")
    else:
        recommendations.append("Urgent reconstruction needed - pavement has failed")
    
    critical_defects = [d for d in detections if d['severity'] == 'critical']
    high_defects = [d for d in detections if d['severity'] == 'high']
    
    if critical_defects:
        for defect in critical_defects[:3]:
            recommendations.append(
                f"URGENT: {defect['type']} repair at location "
                f"({defect['bbox']['x']}, {defect['bbox']['y']}) - safety hazard"
            )
    
    if high_defects:
        defect_types = set(d['type'] for d in high_defects)
        for dtype in defect_types:
            count = len([d for d in high_defects if d['type'] == dtype])
            recommendations.append(
                f"Priority repair: {count} high-severity {dtype}(s) detected"
            )
    
    total_defects = len(detections)
    if total_defects > 0:
        estimated_cost = estimate_repair_cost(detections)
        recommendations.append(
            f"Estimated repair cost: ${estimated_cost:,.0f} - ${estimated_cost * 1.3:,.0f}"
        )
    
    return recommendations

def estimate_repair_cost(detections: List[Dict]) -> float:
    """Estimate costs for YOUR custom defect types"""
    
    # YOUR CUSTOM COST ESTIMATES
    cost_per_defect = {
        'apothole': {'low': 200, 'medium': 350, 'high': 600, 'critical': 1000},
        'spalling': {'low': 150, 'medium': 300, 'high': 500, 'critical': 800},
        'patching': {'low': 100, 'medium': 200, 'high': 350, 'critical': 500},
        'rm': {'low': 300, 'medium': 500, 'high': 800, 'critical': 1200}
    }
    
    total_cost = 0
    
    for detection in detections:
        defect_type = detection['type']
        severity = detection['severity']
        
        if defect_type in cost_per_defect:
            cost = cost_per_defect[defect_type].get(severity, 100)
        else:
            cost = 100
        
        total_cost += cost
    
    return total_cost