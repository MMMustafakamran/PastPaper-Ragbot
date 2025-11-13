"""
Test script for MCQ processor
Tests parsing, classification, and JSON generation on a single file
"""

import json
from mcq_processor import MCQParser, TopicClassifier, JSONGenerator, BatchProcessor


def test_parser():
    """Test MCQ parsing"""
    print("=" * 60)
    print("TEST 1: MCQ Parser")
    print("=" * 60)
    
    parser = MCQParser()
    
    # Test file
    test_file = "data/Standard_text/NET/100_netquestions/NET-Mathematics-100-MCQs(2)(1).doc.txt"
    
    try:
        questions = parser.parse_file(test_file)
        print(f"[PASS] Parsed {len(questions)} questions from {test_file}")
        
        # Show first question
        if questions:
            q = questions[0]
            print(f"\nSample Question:")
            print(f"  Number: {q['number']}")
            print(f"  Text: {q['text'][:100]}...")
            print(f"  Options: {len(q['options'])}")
            print(f"  Answer: {q['answer_key']} → {q['answer_value']}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_classifier():
    """Test topic classification"""
    print("\n" + "=" * 60)
    print("TEST 2: Topic Classifier")
    print("=" * 60)
    
    try:
        classifier = TopicClassifier("Topics_net")
        
        # Test questions
        test_questions = [
            "What is the derivative of x^2?",
            "Find the limit as x approaches 0 of sin(x)/x",
            "If f(x) = x, then f is called what type of function?",
            "Calculate the probability of rolling a 6 on a die"
        ]
        
        for q in test_questions:
            subject, main_topic, sub_topic = classifier.classify(q)
            difficulty = classifier.estimate_difficulty(q)
            
            print(f"\nQuestion: {q}")
            print(f"  → Topic: {main_topic} | Sub-topic: {sub_topic}")
            print(f"  → Difficulty: {difficulty}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_json_generator():
    """Test JSON generation"""
    print("\n" + "=" * 60)
    print("TEST 3: JSON Generator")
    print("=" * 60)
    
    try:
        parser = MCQParser()
        classifier = TopicClassifier("Topics_net")
        generator = JSONGenerator(classifier)
        
        # Parse sample file
        test_file = "data/Standard_text/NET/100_netquestions/NET-Mathematics-100-MCQs(2)(1).doc.txt"
        questions = parser.parse_file(test_file)
        
        if not questions:
            print("[FAIL] No questions to process")
            return False
        
        # Generate dataset
        source_info = {
            "exam_type": "NET",
            "subject": "Mathematics",
            "source_file": "TEST_FILE.txt",
            "paper_name": "Test Paper",
            "year": "2024"
        }
        
        datasets = generator.generate_dataset(questions[:5], source_info)
        
        print(f"[PASS] Generated {len(datasets)} topic datasets")
        
        for topic, dataset in datasets.items():
            print(f"\n  Topic: {topic}")
            print(f"    Questions: {dataset['dataset_info']['total_questions']}")
            
            # Show sample question structure
            if dataset['questions']:
                q = dataset['questions'][0]
                print(f"    Sample ID: {q['question_id']}")
                print(f"    Embedding text: {q['embedding_text'][:100]}...")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_processor():
    """Test batch processing (single file)"""
    print("\n" + "=" * 60)
    print("TEST 4: Batch Processor (Single File)")
    print("=" * 60)
    
    try:
        processor = BatchProcessor(
            topics_file="Topics_net",
            output_dir="processed_data_test"
        )
        
        # Process single file
        test_file = "data/Standard_text/NET/100_netquestions/NET-Mathematics-100-MCQs(2)(1).doc.txt"
        processor.process_file(test_file)
        
        print("\n[PASS] Processing complete!")
        print("  Check 'processed_data_test/' for output files")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_json_validation():
    """Validate generated JSON"""
    print("\n" + "=" * 60)
    print("TEST 5: JSON Validation")
    print("=" * 60)
    
    try:
        import os
        test_dir = "processed_data_test"
        
        if not os.path.exists(test_dir):
            print("[FAIL] No test output directory found. Run test_batch_processor first.")
            return False
        
        # Find JSON files
        json_files = []
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        if not json_files:
            print("✗ No JSON files found")
            return False
        
        print(f"Found {len(json_files)} JSON files:\n")
        
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            assert "dataset_info" in data, "Missing dataset_info"
            assert "questions" in data, "Missing questions"
            
            info = data["dataset_info"]
            questions = data["questions"]
            
            print(f"✓ {json_file}")
            print(f"  Name: {info['dataset_name']}")
            print(f"  Questions: {len(questions)}")
            print(f"  Declared: {info['total_questions']}")
            
            # Validate first question
            if questions:
                q = questions[0]
                required_fields = [
                    "question_id", "source", "topic", "question", 
                    "options", "answer", "embedding_text", "metadata"
                ]
                
                for field in required_fields:
                    assert field in q, f"Missing field: {field}"
                
                print(f"  ✓ All required fields present")
            
            print()
        
        return True
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MCQ PROCESSOR TEST SUITE")
    print("=" * 60 + "\n")
    
    results = {
        "Parser": test_parser(),
        "Classifier": test_classifier(),
        "JSON Generator": test_json_generator(),
        "Batch Processor": test_batch_processor(),
        "JSON Validation": test_json_validation()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:20s}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("\nYou can now run: python mcq_processor.py")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease fix errors before processing all files")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

