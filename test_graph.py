# test_graph.py
from app.agents.graph import assessment_graph
import os

print("Testing LangGraph Assessment Workflow...")
print("="*60)

# You need a test image - let's create a dummy path for now
test_image = "test_image.jpg"

# Check if test image exists
if not os.path.exists(test_image):
    print(f"⚠️  Test image '{test_image}' not found")
    print("\nTo test the workflow:")
    print("1. Place a pavement image as 'test_image.jpg'")
    print("2. Run: python test_graph.py")
    print("\nWorkflow is ready to use!")
else:
    print(f"Running workflow on: {test_image}\n")
    
    # Run workflow
    result = assessment_graph.invoke({
        "image_path": test_image,
        "detections": [],
        "annotated_image_path": "",
        "pci_score": 0.0,
        "condition": "",
        "analysis": "",
        "recommendations": [],
        "messages": [],
        "error": ""
    })
    
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    print(f"Detections: {len(result['detections'])}")
    print(f"PCI Score: {result['pci_score']}")
    print(f"Condition: {result['condition']}")
    print(f"\nAnalysis:\n{result['analysis']}")