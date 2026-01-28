# app/agents/tools.py
from typing import Dict, List, Optional
from app.models.pci_calculator import estimate_repair_cost
from datetime import datetime, timedelta


# app/agents/tools.py

# Add this import at the top
from sqlalchemy import text
from typing import List, Dict

# Add this function at the end of the file

def execute_sql_query(query: str, db_connection_string: str) -> str:
    """
    Execute SQL query and return formatted results
    
    Args:
        query: SQL query string
        db_connection_string: Database connection string
        
    Returns:
        Formatted query results
    """
    from sqlalchemy import create_engine
    import pandas as pd
    
    try:
        # Validate query (read-only safety)
        query_upper = query.upper().strip()
        
        # Block dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'CREATE']
        if any(keyword in query_upper for keyword in dangerous_keywords):
            return "❌ Only SELECT queries are allowed for safety."
        
        # Create engine
        engine = create_engine(db_connection_string)
        
        # Execute query
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return "No results found."
        
        # Format results
        result = f"**Query Results:** ({len(df)} rows)\n\n"
        
        # Convert to markdown table
        result += df.to_markdown(index=False)
        
        return result
        
    except Exception as e:
        return f"❌ SQL Error: {str(e)}"

def analyze_query_intent(question: str) -> bool:
    """
    Determine if question requires SQL query
    
    Args:
        question: User's question
        
    Returns:
        True if SQL query needed
    """
    sql_keywords = [
        'show', 'list', 'find', 'get', 'count', 'how many',
        'all', 'total', 'average', 'sum', 'maximum', 'minimum',
        'where', 'filter', 'search', 'query', 'select'
    ]
    
    question_lower = question.lower()
    
    # Check if question contains SQL-like intent
    return any(keyword in question_lower for keyword in sql_keywords)

def get_defect_statistics(detections: List[Dict]) -> str:
    """
    Get statistics about detected defects
    
    Args:
        detections: List of defect detections
        
    Returns:
        Formatted statistics string
    """
    if not detections:
        return "No defects detected"
    
    # Count by type
    by_type = {}
    by_severity = {}
    
    for det in detections:
        dtype = det['type']
        severity = det['severity']
        
        by_type[dtype] = by_type.get(dtype, 0) + 1
        by_severity[severity] = by_severity.get(severity, 0) + 1
    
    # Format output
    stats = f"**Total Defects:** {len(detections)}\n\n"
    
    stats += "**By Type:**\n"
    for dtype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        stats += f"  - {dtype}: {count}\n"
    
    stats += "\n**By Severity:**\n"
    severity_order = ['critical', 'high', 'medium', 'low']
    for sev in severity_order:
        if sev in by_severity:
            stats += f"  - {sev}: {by_severity[sev]}\n"
    
    return stats

def get_repair_cost_breakdown(detections: List[Dict]) -> str:
    """
    Get detailed repair cost breakdown
    
    Args:
        detections: List of defect detections
        
    Returns:
        Formatted cost breakdown
    """
    if not detections:
        return "No repairs needed"
    
    total_cost = estimate_repair_cost(detections)
    
    # Calculate by type
    cost_by_type = {}
    
    cost_per_defect = {
        'pothole': {'low': 200, 'medium': 350, 'high': 600, 'critical': 1000},
        'cavity': {'low': 200, 'medium': 350, 'high': 600, 'critical': 1000},
        'alligator_crack': {'low': 150, 'medium': 300, 'high': 500, 'critical': 800},
        'crack': {'low': 75, 'medium': 150, 'high': 250, 'critical': 400},
        'rutting': {'low': 300, 'medium': 500, 'high': 800, 'critical': 1200},
        'patch': {'low': 100, 'medium': 200, 'high': 350, 'critical': 500},
        'manhole': {'low': 150, 'medium': 250, 'high': 400, 'critical': 600}
    }
    
    for det in detections:
        dtype = det['type']
        severity = det['severity']
        
        if dtype in cost_per_defect:
            cost = cost_per_defect[dtype].get(severity, 100)
        else:
            cost = 100
        
        cost_by_type[dtype] = cost_by_type.get(dtype, 0) + cost
    
    # Format breakdown
    breakdown = f"**Total Estimated Cost:** ${total_cost:,.0f}\n\n"
    breakdown += "**Breakdown by Defect Type:**\n"
    
    for dtype, cost in sorted(cost_by_type.items(), key=lambda x: x[1], reverse=True):
        percentage = (cost / total_cost) * 100
        breakdown += f"  - {dtype}: ${cost:,.0f} ({percentage:.1f}%)\n"
    
    breakdown += f"\n**Range:** ${total_cost * 0.8:,.0f} - ${total_cost * 1.3:,.0f}"
    breakdown += "\n*(Includes labor, materials, and traffic control)*"
    
    return breakdown

def get_priority_repairs(detections: List[Dict], top_n: int = 5) -> str:
    """
    Get list of priority repairs
    
    Args:
        detections: List of defect detections
        top_n: Number of top priority items
        
    Returns:
        Formatted priority list
    """
    if not detections:
        return "No repairs needed"
    
    # Sort by severity and size
    severity_weight = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
    
    sorted_detections = sorted(
        detections,
        key=lambda x: (severity_weight.get(x['severity'], 0), x.get('area_pixels', 0)),
        reverse=True
    )
    
    priorities = "**Priority Repair List:**\n\n"
    
    for i, det in enumerate(sorted_detections[:top_n], 1):
        priorities += f"{i}. **{det['type'].upper()}** - {det['severity']} severity\n"
        priorities += f"   Location: ({det['bbox']['x']}, {det['bbox']['y']})\n"
        priorities += f"   Size: {det['bbox']['width']}x{det['bbox']['height']} pixels\n"
        priorities += f"   Confidence: {det['confidence']:.2f}\n\n"
    
    return priorities

def get_timeline_estimate(pci_score: float, detections: List[Dict]) -> str:
    """
    Estimate repair timeline based on PCI and defects
    
    Args:
        pci_score: PCI score
        detections: List of detections
        
    Returns:
        Timeline recommendations
    """
    critical_count = len([d for d in detections if d['severity'] == 'critical'])
    high_count = len([d for d in detections if d['severity'] == 'high'])
    
    timeline = "**Recommended Repair Timeline:**\n\n"
    
    # Immediate (within 48 hours)
    if critical_count > 0:
        timeline += f"**IMMEDIATE (24-48 hours):**\n"
        timeline += f"  - {critical_count} critical defect(s) - safety hazard\n"
        timeline += f"  - Temporary barriers/signage required\n\n"
    
    # Urgent (within 2 weeks)
    if high_count > 0:
        timeline += f"**URGENT (1-2 weeks):**\n"
        timeline += f"  - {high_count} high-severity defect(s)\n"
        timeline += f"  - Schedule repair crews\n\n"
    
    # Short-term based on PCI
    if pci_score < 55:
        timeline += f"**SHORT-TERM (1-3 months):**\n"
        timeline += f"  - Major rehabilitation required\n"
        timeline += f"  - Current PCI: {pci_score} (Fair condition)\n\n"
    elif pci_score < 70:
        timeline += f"**MEDIUM-TERM (3-6 months):**\n"
        timeline += f"  - Corrective maintenance\n"
        timeline += f"  - Current PCI: {pci_score} (Good condition)\n\n"
    else:
        timeline += f"**LONG-TERM (6-12 months):**\n"
        timeline += f"  - Preventive maintenance\n"
        timeline += f"  - Current PCI: {pci_score} (Very Good/Excellent)\n\n"
    
    # Re-assessment
    timeline += f"**RE-ASSESSMENT:**\n"
    if pci_score < 40:
        timeline += f"  - Weekly monitoring recommended\n"
    elif pci_score < 70:
        timeline += f"  - Monthly inspection recommended\n"
    else:
        timeline += f"  - Quarterly inspection sufficient\n"
    
    return timeline