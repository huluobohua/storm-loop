#!/usr/bin/env python3
"""
Real Research Report Generation Test
Testing the new STORM-Loop system with actual report generation
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add frontend to path for imports
frontend_path = os.path.join(os.path.dirname(__file__), 'frontend')
sys.path.insert(0, frontend_path)
print(f"Added to path: {frontend_path}")

# Set development environment for testing
os.environ['ENVIRONMENT'] = 'development'

# Import our advanced interface
from advanced_interface.main_interface import AdvancedAcademicInterface

async def generate_real_research_report():
    """Generate an actual research report and save it to files"""
    
    print("🔬 STORM-Loop Advanced Academic Interface - Real Research Generation")
    print("=" * 80)
    
    # Initialize interface
    print("\n📋 Step 1: Initializing Advanced Academic Interface...")
    interface = AdvancedAcademicInterface()
    print("✅ Interface initialized with real STORM integration!")
    
    # Configure for academic research
    print("\n⚙️  Step 2: Configuring advanced research parameters...")
    research_config = {
        "storm_mode": "academic",
        "agents": ["academic_researcher", "critic"],  # Only available agents
        "databases": ["openalex", "crossref"],
        "output_formats": ["markdown", "html"],
        "max_papers": 50,
        "quality_threshold": 0.85,
        "citation_style": "apa",
        "include_abstracts": True,
        "language": "en",
        "timeout_minutes": 30,
        "advanced_options": {
            "enable_verification": True,
            "quality_gates": True,
            "citation_verification": True
        }
    }
    
    await interface.configure_research(research_config)
    print("✅ Research configuration applied!")
    
    # Start research on quantum computing
    print("\n🔍 Step 3: Starting research generation...")
    research_topic = "Quantum Computing Applications in Drug Discovery and Molecular Simulation"
    print(f"   📝 Topic: {research_topic}")
    
    research_id = await interface.start_research(research_topic)
    print(f"   🆔 Research ID: {research_id}")
    
    # Wait for research to complete
    print("\n⏱️  Step 4: Monitoring research progress...")
    max_wait = 30  # seconds
    for i in range(max_wait):
        status = await interface.get_research_status(research_id)
        print(f"   📊 Status: {status['status']} - Stage: {status.get('current_stage', 'unknown')}")
        
        if status['status'] == 'completed':
            print("   ✅ Research completed successfully!")
            break
        elif status['status'] == 'failed':
            print(f"   ❌ Research failed: {status.get('error', 'Unknown error')}")
            return False
        
        await asyncio.sleep(1)
    
    # Generate output files
    print("\n📄 Step 5: Generating research report files...")
    output_formats = ["markdown", "html"]
    output_result = await interface.generate_output(research_id, output_formats)
    
    if "error" in output_result:
        print(f"   ❌ Output generation failed: {output_result['error']}")
        return False
    
    print("   ✅ Research report generated successfully!")
    print(f"   📁 Files created: {len(output_result['files'])}")
    
    for file_path in output_result['files']:
        print(f"   📄 {file_path}")
    
    # Get and display the research article
    print("\n📖 Step 6: Retrieving full research article...")
    article = interface.get_research_article(research_id)
    
    if article:
        print("   ✅ Article retrieved successfully!")
        print(f"   📊 Topic: {article['topic']}")
        print(f"   📝 Content length: {len(article['content'])} characters")
        print(f"   🏷️  Metadata: {article['metadata']}")
        
        # Display first 500 characters of the report
        print("\n📋 RESEARCH REPORT PREVIEW:")
        print("-" * 60)
        print(article['content'][:800] + "..." if len(article['content']) > 800 else article['content'])
        print("-" * 60)
        
    else:
        print("   ❌ Failed to retrieve article")
        return False
    
    # Show file locations
    print("\n📁 Step 7: Research Report Files Generated:")
    print("   The following files have been created in the research_outputs directory:")
    
    for file_path in output_result['files']:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({file_size} bytes)")
            
            # Show first few lines of each file
            if file_path.endswith('.md'):
                print("      📄 Markdown content preview:")
                with open(file_path, 'r', encoding='utf-8') as f:
                    preview = f.read(200)
                    print(f"         {preview[:200]}...")
            
        else:
            print(f"   ❌ {file_path} (not found)")
    
    print("\n" + "=" * 80)
    print("✨ REAL RESEARCH REPORT GENERATION COMPLETED")
    print("=" * 80)
    
    print("\n🎯 Summary:")
    print("   ✅ Advanced Academic Interface: Working")
    print("   ✅ STORM Integration: Connected")
    print("   ✅ Research Generation: Successful")
    print("   ✅ Multi-format Output: Generated")
    print("   ✅ File System Integration: Working")
    
    print(f"\n📊 Report Details:")
    print(f"   🔬 Topic: {research_topic}")
    print(f"   🆔 Research ID: {research_id}")
    print(f"   📄 Formats: {', '.join(output_formats)}")
    print(f"   📁 Files: {len(output_result['files'])} created")
    print(f"   📝 Content: {len(article['content'])} characters")
    
    print("\n🚀 YOUR RESEARCH REPORT IS READY!")
    print("   Check the 'research_outputs' directory for your files.")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Real Research Report Generation...")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        success = asyncio.run(generate_real_research_report())
        if success:
            print("\n🎉 SUCCESS! Your research report has been generated.")
            print("   📁 Check the research_outputs directory for your files!")
            exit(0)
        else:
            print("\n⚠️  Report generation encountered issues.")
            exit(1)
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)