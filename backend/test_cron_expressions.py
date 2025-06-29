#!/usr/bin/env python3
"""
Test cron expression parsing and validation
"""
from datetime import datetime, timezone
from croniter import croniter


def test_cron_expressions():
    """Test various cron expressions"""
    expressions = [
        ("*/5 * * * *", "Every 5 minutes"),
        ("0 * * * *", "Every hour"),
        ("0 9 * * *", "Daily at 9 AM"),
        ("0 0 * * 0", "Weekly on Sunday at midnight"),
        ("0 0 1 * *", "Monthly on the 1st"),
        ("30 2 15 * *", "Monthly on 15th at 2:30 AM"),
        ("0 */4 * * *", "Every 4 hours"),
        ("0 9-17 * * 1-5", "Hourly 9 AM - 5 PM on weekdays"),
        ("*/15 * * * *", "Every 15 minutes"),
        ("0 0 * * *", "Daily at midnight"),
    ]
    
    print("Cron Expression Testing")
    print("=" * 80)
    
    base_time = datetime.now(timezone.utc)
    
    for expr, description in expressions:
        print(f"\nExpression: {expr}")
        print(f"Description: {description}")
        
        try:
            cron = croniter(expr, base_time)
            print("Valid: ✓")
            
            # Show next 5 occurrences
            print("Next 5 runs:")
            for i in range(5):
                next_time = cron.get_next(datetime)
                print(f"  {i+1}. {next_time}")
                
        except Exception as e:
            print(f"Valid: ✗ ({e})")
    
    print("\n" + "=" * 80)
    print("\nTesting complete!")


if __name__ == "__main__":
    test_cron_expressions()