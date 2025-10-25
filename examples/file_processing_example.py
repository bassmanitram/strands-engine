#!/usr/bin/env python3
"""
File Processing Example for strands_agent_factory.

This example demonstrates how to upload and process various file types
with the agent factory, including dynamic file references.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from strands_agent_factory import AgentFactoryConfig, AgentFactory


def create_example_files():
    """Create example files for processing."""
    
    # Create temporary directory
    files_dir = Path(tempfile.mkdtemp(prefix="strands_files_"))
    
    # Create various file types
    
    # 1. Text file
    text_file = files_dir / "sample.txt"
    text_file.write_text("""This is a sample text file for processing.
It contains multiple lines of text that demonstrate
how the agent factory can process text documents.

Key points:
- Text files are processed as documents
- Content is extracted and made available to the agent
- The agent can analyze and work with the content
""")
    
    # 2. JSON file
    json_file = files_dir / "data.json"
    json_data = {
        "users": [
            {"id": 1, "name": "Alice", "age": 30, "city": "New York"},
            {"id": 2, "name": "Bob", "age": 25, "city": "San Francisco"},
            {"id": 3, "name": "Charlie", "age": 35, "city": "Chicago"}
        ],
        "metadata": {
            "total_users": 3,
            "created_at": "2024-01-15",
            "version": "1.0"
        }
    }
    json_file.write_text(json.dumps(json_data, indent=2))
    
    # 3. CSV file
    csv_file = files_dir / "sales.csv"
    csv_file.write_text("""Date,Product,Quantity,Price,Total
2024-01-01,Widget A,10,25.50,255.00
2024-01-02,Widget B,5,30.00,150.00
2024-01-03,Widget A,8,25.50,204.00
2024-01-04,Widget C,12,15.75,189.00
2024-01-05,Widget B,7,30.00,210.00
""")
    
    # 4. Markdown file
    md_file = files_dir / "report.md"
    md_file.write_text("""# Monthly Report

## Summary
This month showed strong performance across all metrics.

## Key Metrics
- **Sales**: $1,008.00 total revenue
- **Units Sold**: 42 units
- **Top Product**: Widget B (highest price per unit)

## Analysis
The data shows consistent demand for Widget A and Widget B,
with Widget C showing potential for growth.

### Recommendations
1. Increase inventory for Widget A and B
2. Consider promotional pricing for Widget C
3. Monitor trends for next month
""")
    
    # 5. Python code file
    py_file = files_dir / "example.py"
    py_file.write_text('''#!/usr/bin/env python3
"""
Example Python script for analysis.
"""

def calculate_total_sales(sales_data):
    """Calculate total sales from sales data."""
    total = 0
    for item in sales_data:
        total += item.get('total', 0)
    return total


def find_top_product(sales_data):
    """Find the product with highest total sales."""
    product_totals = {}
    for item in sales_data:
        product = item.get('product', 'Unknown')
        total = item.get('total', 0)
        product_totals[product] = product_totals.get(product, 0) + total
    
    return max(product_totals.items(), key=lambda x: x[1])


if __name__ == "__main__":
    # Example usage
    sales = [
        {"product": "Widget A", "total": 255.00},
        {"product": "Widget B", "total": 150.00},
    ]
    
    print(f"Total sales: ${calculate_total_sales(sales)}")
    print(f"Top product: {find_top_product(sales)}")
''')
    
    return files_dir, {
        'text': text_file,
        'json': json_file,
        'csv': csv_file,
        'markdown': md_file,
        'python': py_file
    }


async def basic_file_processing_example():
    """Demonstrate basic file processing."""
    print("Basic File Processing Example")
    print("=" * 40)
    
    # Create example files
    files_dir, files = create_example_files()
    
    try:
        # Configure agent with file uploads
        config = AgentFactoryConfig(
            model="gpt-4o",
            system_prompt="You are a helpful assistant that can analyze uploaded files. Provide insights about the content and structure of the files.",
            file_paths=[
                (str(files['text']), "text/plain"),
                (str(files['json']), "application/json"),
                (str(files['csv']), "text/csv"),
                (str(files['markdown']), "text/markdown"),
                (str(files['python']), "text/plain"),
            ],
            initial_message="I've uploaded several files for analysis. Please examine them and provide a summary of what you found."
        )
        
        factory = AgentFactory(config)
        await factory.initialize()
        agent = factory.create_agent()
        
        print(f"Created agent with {len(config.file_paths)} uploaded files")
        print("Files uploaded:")
        for file_path, mimetype in config.file_paths:
            print(f"  - {Path(file_path).name} ({mimetype})")
        
        # The initial message will be sent automatically with the files
        with agent as a:
            # Ask follow-up questions
            follow_up_queries = [
                "Can you analyze the sales data in the CSV file and tell me the total revenue?",
                "What insights can you provide about the user data in the JSON file?",
                "Can you explain what the Python code does?",
                "Based on all the files, what recommendations would you make?"
            ]
            
            for query in follow_up_queries:
                print(f"\n{'='*50}")
                print(f"Query: {query}")
                print("-" * 50)
                
                success = await a.send_message_to_agent(query, show_user_input=False)
                if not success:
                    print("Failed to process query")
                    
    except Exception as e:
        print(f"Basic file processing error: {e}")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(files_dir)
        print(f"\nCleaned up files directory: {files_dir}")


async def dynamic_file_reference_example():
    """Demonstrate dynamic file references using file() syntax."""
    print("Dynamic File Reference Example")
    print("=" * 40)
    
    # Create example files
    files_dir, files = create_example_files()
    
    try:
        # Configure agent without pre-uploaded files
        config = AgentFactoryConfig(
            model="gpt-4o",
            system_prompt="You are a helpful assistant that can work with files referenced dynamically in messages.",
        )
        
        factory = AgentFactory(config)
        await factory.initialize()
        agent = factory.create_agent()
        
        print("Created agent for dynamic file processing")
        print("Files available for dynamic reference:")
        for name, file_path in files.items():
            print(f"  - {file_path}")
        
        # Use dynamic file references in messages
        with agent as a:
            # Reference specific files dynamically
            message_with_files = f"""
Please analyze the following files:

file('{files['csv']}', 'text/csv')
file('{files['json']}', 'application/json')

Can you compare the data in these two files and provide insights?
"""
            
            print(f"\n{'='*50}")
            print("Message with dynamic file references:")
            print(message_with_files)
            print("-" * 50)
            
            success = await a.send_message_to_agent(message_with_files, show_user_input=False)
            if not success:
                print("Failed to process message with file references")
            
            # Use glob patterns for multiple files
            glob_message = f"""
Please analyze all files in this directory:

file('{files_dir}/*.txt')
file('{files_dir}/*.md')

What common themes do you see across these text-based files?
"""
            
            print(f"\n{'='*50}")
            print("Message with glob patterns:")
            print(glob_message)
            print("-" * 50)
            
            success = await a.send_message_to_agent(glob_message, show_user_input=False)
            if not success:
                print("Failed to process message with glob patterns")
                
    except Exception as e:
        print(f"Dynamic file reference error: {e}")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(files_dir)
        print(f"\nCleaned up files directory: {files_dir}")


async def mixed_file_processing_example():
    """Demonstrate mixing pre-uploaded files with dynamic references."""
    print("Mixed File Processing Example")
    print("=" * 40)
    
    # Create example files
    files_dir, files = create_example_files()
    
    try:
        # Configure agent with some pre-uploaded files
        config = AgentFactoryConfig(
            model="gpt-4o",
            system_prompt="You are a data analyst with access to both pre-loaded and dynamically referenced files.",
            file_paths=[
                (str(files['json']), "application/json"),  # Pre-upload JSON
                (str(files['csv']), "text/csv"),           # Pre-upload CSV
            ],
            initial_message="I've pre-loaded some data files. Please provide an initial analysis."
        )
        
        factory = AgentFactory(config)
        await factory.initialize()
        agent = factory.create_agent()
        
        print("Created agent with pre-uploaded files and dynamic reference capability")
        print("Pre-uploaded files:")
        for file_path, mimetype in config.file_paths:
            print(f"  - {Path(file_path).name} ({mimetype})")
        
        # The initial analysis will happen automatically
        with agent as a:
            # Now reference additional files dynamically
            dynamic_message = f"""
Now I want to add more context to your analysis. Please also examine:

file('{files['markdown']}', 'text/markdown')
file('{files['python']}', 'text/plain')

How do these additional files relate to the data you already analyzed?
Can you provide a comprehensive report combining all the information?
"""
            
            print(f"\n{'='*50}")
            print("Adding dynamic file references to existing analysis:")
            print("-" * 50)
            
            success = await a.send_message_to_agent(dynamic_message, show_user_input=False)
            if not success:
                print("Failed to process dynamic file addition")
                
    except Exception as e:
        print(f"Mixed file processing error: {e}")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(files_dir)
        print(f"\nCleaned up files directory: {files_dir}")


def main():
    """Main example selector."""
    print("File Processing Examples")
    print("=" * 30)
    print("1. Basic File Processing (Pre-uploaded)")
    print("2. Dynamic File References")
    print("3. Mixed File Processing")
    print("4. All Examples")
    
    choice = input("\nSelect example [1-4]: ").strip()
    
    if choice == "1":
        asyncio.run(basic_file_processing_example())
    elif choice == "2":
        asyncio.run(dynamic_file_reference_example())
    elif choice == "3":
        asyncio.run(mixed_file_processing_example())
    elif choice == "4":
        asyncio.run(basic_file_processing_example())
        asyncio.run(dynamic_file_reference_example())
        asyncio.run(mixed_file_processing_example())
    else:
        print("Invalid choice. Running basic file processing example...")
        asyncio.run(basic_file_processing_example())


if __name__ == "__main__":
    """
    Run the file processing examples.
    
    Prerequisites:
    - Set OPENAI_API_KEY environment variable
    - Install strands-agent-factory
    
    Usage:
        python examples/file_processing_example.py
    """
    
    print("File Processing Examples")
    print("=" * 30)
    print("Prerequisites:")
    print("- Set OPENAI_API_KEY environment variable")
    print("- Install: pip install 'strands-agent-factory[openai]'")
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Unexpected error: {e}")