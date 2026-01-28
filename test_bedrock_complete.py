# test_aws_complete.py
"""
Complete AWS Bedrock connection test
Tests credentials, connection, and Claude model access
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(text)
    print("="*60)

def print_step(number, text):
    """Print step number"""
    print(f"\n{number}. {text}")

def print_success(text):
    """Print success message"""
    print(f"   ✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"   ❌ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"   ⚠️  {text}")

def check_credentials():
    """Check if AWS credentials are set"""
    print_step(1, "Checking AWS credentials...")
    
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    
    print(f"   Region: {aws_region}")
    
    if aws_key:
        print(f"   Access Key: {aws_key[:10]}...{aws_key[-4:]}")
    else:
        print_error("AWS_ACCESS_KEY_ID not found in .env")
        return False
    
    if aws_secret:
        print(f"   Secret Key: {'*' * 20}...{aws_secret[-4:]}")
    else:
        print_error("AWS_SECRET_ACCESS_KEY not found in .env")
        return False
    
    print_success("Credentials loaded from .env")
    return True

def test_boto3():
    """Test if boto3 is installed"""
    print_step(2, "Checking boto3 installation...")
    
    try:
        import boto3
        version = boto3.__version__
        print_success(f"boto3 version {version} installed")
        return True
    except ImportError:
        print_error("boto3 not installed")
        print("\n   Install with: pip install boto3")
        return False

def test_bedrock_client():
    """Test Bedrock client creation"""
    print_step(3, "Creating Bedrock client...")
    
    try:
        import boto3
        from botocore.config import Config
        
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        
        config = Config(
            region_name=aws_region,
            signature_version='v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=aws_region,
            config=config
        )
        
        print_success("Bedrock client created successfully")
        return bedrock
        
    except Exception as e:
        print_error(f"Failed to create Bedrock client: {e}")
        return None

def test_claude_model(bedrock_client):
    """Test Claude model invocation"""
    print_step(4, "Testing Claude 3.5 Sonnet model...")
    
    if not bedrock_client:
        print_error("Bedrock client not available")
        return False
    
    try:
        import json
        from botocore.exceptions import ClientError
        
        # Prepare request
        #model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        print(f"   Model ID: {model_id}")
        print(f"   Sending test message...")
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Respond with exactly: 'AWS Bedrock is working perfectly!' and nothing else."
                }
            ],
            "temperature": 0
        }
        
        # Invoke model
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        ai_response = response_body['content'][0]['text']
        
        print_success(f"Claude responded: '{ai_response}'")
        
        # Check tokens used
        usage = response_body.get('usage', {})
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
        
        print(f"   📊 Tokens used: Input={input_tokens}, Output={output_tokens}")
        print(f"   💰 Estimated cost: ~$0.0001")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        print_error(f"AWS Error: {error_code}")
        print(f"   Message: {error_msg}")
        
        if "AccessDeniedException" in error_code:
            print("\n   🔧 Possible fixes:")
            print("   1. Check IAM user has 'AmazonBedrockFullAccess' policy")
            print("   2. Wait a few minutes if you just created the user")
            print("   3. Try using model in AWS Console Playground first")
            
        elif "ResourceNotFoundException" in error_code:
            print("\n   🔧 Possible fixes:")
            print("   1. Model auto-enables on first use (new AWS feature)")
            print("   2. Try the model in Bedrock Playground first:")
            print("      AWS Console → Bedrock → Playgrounds → Chat")
            print("   3. Select 'Claude 3.5 Sonnet v2' and send a message")
            print("   4. If prompted, fill out Anthropic use case form")
            print("   5. Wait 5-10 minutes and try again")
            
        elif "ThrottlingException" in error_code:
            print("\n   🔧 Fix: Wait a few seconds and try again")
            
        else:
            print(f"\n   🔧 Check AWS Console for more details")
            print(f"   Region: {os.getenv('AWS_REGION', 'us-east-1')}")
        
        return False
        
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        print("\n   Full traceback:")
        traceback.print_exc()
        return False

def test_langchain_integration():
    """Test LangChain AWS integration"""
    print_step(5, "Testing LangChain integration...")
    
    try:
        from langchain_aws import ChatBedrock
        from langchain_core.messages import HumanMessage
        
        print_success("LangChain AWS package available")
        
        # Create LangChain client
        llm = ChatBedrock(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            model_kwargs={
                "temperature": 0,
                "max_tokens": 100
            }
        )
        
        print(f"   Testing LangChain invocation...")
        
        # Test invocation
        response = llm.invoke([
            HumanMessage(content="Say 'LangChain integration works!' and nothing else.")
        ])
        
        print_success(f"LangChain response: '{response.content}'")
        
        return True
        
    except ImportError:
        print_warning("langchain-aws not installed")
        print("   Install with: pip install langchain-aws")
        print("   (Not critical - boto3 works)")
        return False
        
    except Exception as e:
        print_warning(f"LangChain test failed: {e}")
        print("   (Not critical - boto3 works)")
        return False

def run_all_tests():
    """Run all tests"""
    print_header("AWS Bedrock Connection Test Suite")
    
    # Track results
    results = {
        'credentials': False,
        'boto3': False,
        'bedrock_client': False,
        'claude_model': False,
        'langchain': False
    }
    
    # Run tests
    results['credentials'] = check_credentials()
    
    if not results['credentials']:
        print_header("❌ FAILED: Missing AWS credentials")
        print("\nPlease set in .env file:")
        print("AWS_ACCESS_KEY_ID=your-access-key")
        print("AWS_SECRET_ACCESS_KEY=your-secret-key")
        print("AWS_REGION=us-east-1")
        return False
    
    results['boto3'] = test_boto3()
    
    if not results['boto3']:
        print_header("❌ FAILED: boto3 not installed")
        return False
    
    bedrock_client = test_bedrock_client()
    results['bedrock_client'] = bedrock_client is not None
    
    if results['bedrock_client']:
        results['claude_model'] = test_claude_model(bedrock_client)
    
    # Optional LangChain test
    results['langchain'] = test_langchain_integration()
    
    # Print summary
    print_header("Test Summary")
    
    print("\n✅ Passed Tests:")
    for test, passed in results.items():
        if passed:
            print(f"   ✅ {test.replace('_', ' ').title()}")
    
    if not all([results['credentials'], results['boto3'], 
                results['bedrock_client'], results['claude_model']]):
        print("\n❌ Failed Tests:")
        for test, passed in results.items():
            if not passed and test != 'langchain':  # LangChain is optional
                print(f"   ❌ {test.replace('_', ' ').title()}")
    
    # Final verdict
    core_tests_passed = all([
        results['credentials'],
        results['boto3'],
        results['bedrock_client'],
        results['claude_model']
    ])
    
    if core_tests_passed:
        print_header("🎉 SUCCESS! AWS Bedrock is fully configured!")
        print("\n✅ You can now:")
        print("   1. Run FastAPI backend: uvicorn app.main:app --reload")
        print("   2. Test with real pavement images")
        print("   3. Get AI analysis from Claude")
        print("   4. Build the Gradio frontend")
        print("\n💰 Cost estimate for demo: $2-5 total")
        print("📚 Next: Build Gradio frontend")
        return True
    else:
        print_header("❌ SETUP INCOMPLETE")
        print("\nPlease fix the failed tests above before proceeding.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)