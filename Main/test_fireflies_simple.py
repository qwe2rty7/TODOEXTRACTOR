from fireflies_monitor import FirefliesMonitor

def test_fireflies():
    print("Testing Fireflies Monitor...")
    print("=" * 50)
    
    monitor = FirefliesMonitor()
    
    # Check for transcripts once
    monitor.check_new_transcripts()
    
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    test_fireflies()