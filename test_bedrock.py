# test_bedrock.py
import os

# Check if AWS credentials are set
if not os.getenv("AWS_ACCESS_KEY_ID"):
    print("⚠️  AWS credentials not set")
    print("\nTo test Bedrock:")
    print("1. Get AWS credentials from AWS Console")
    print("2. Set in .env file:")
    print("   AWS_ACCESS_KEY_ID=AKIA...")
    print("   AWS_SECRET_ACCESS_KEY=...")
    print("3. Enable Bedrock in AWS Console")
    print("\nSkipping Bedrock test for now...")
else:
    print("Testing AWS Bedrock connection...")
    from app.core.aws_bedrock import get_bedrock_client
    
    try:
        client = get_bedrock_client()
        
        # Test connection
        if client.test_connection():
            print("\n✅ AWS Bedrock connection successful!")
            
            # Test analysis
            print("\nTesting pavement analysis...")
            test_detections = [
                {
                    'type': 'pothole',
                    'severity': 'high',
                    'confidence': 0.92,
                    'bbox': {'x': 100, 'y': 200, 'width': 150, 'height': 120}
                }
            ]
            
            analysis = client.analyze_pavement(
                pci_score=65,
                detections=test_detections
            )
            
            print("\n" + "="*60)
            print("Sample Analysis:")
            print("="*60)
            print(analysis)
            print("="*60)
        else:
            print("\n❌ Connection test failed")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. AWS credentials are correct")
        print("2. Bedrock is enabled in your AWS account")
        print("3. Claude model access is granted")