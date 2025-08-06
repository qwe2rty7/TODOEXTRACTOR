import os
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import requests
import anthropic
from todo_manager import TodoManager

load_dotenv()

class FirefliesMonitor:
    def __init__(self):
        self.fireflies_api_key = os.getenv('FIREFLIES_API_KEY')
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.user_email = os.getenv('USER_EMAIL')
        
        # GraphQL endpoint
        self.api_url = "https://api.fireflies.ai/graphql"
        
        # Initialize Claude client
        if self.claude_api_key:
            self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
        else:
            self.claude_client = None
        
        # Initialize todo manager
        self.todo_manager = TodoManager()
        
        # Track last check time for transcripts
        self.last_transcript_check = datetime.now(timezone.utc) - timedelta(hours=1)
    
    def get_recent_transcripts(self, hours_back=1):
        """Fetch transcripts from the last X hours"""
        if not self.fireflies_api_key:
            print("❌ Fireflies API key not configured")
            return []
        
        headers = {
            'Authorization': f'Bearer {self.fireflies_api_key}',
            'Content-Type': 'application/json'
        }
        
        # Calculate time filter - Fireflies uses ISO format
        from_date = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # GraphQL query to get recent transcripts
        query = """
        query GetRecentTranscripts($fromDate: DateTime!, $participantEmail: String) {
          transcripts(
            fromDate: $fromDate
            participant_email: $participantEmail
            limit: 20
          ) {
            id
            title
            date
            organizer_email
            participants {
              name
              email
            }
            summary {
              action_items
              overview
            }
            sentences {
              text
              speaker_name
              speaker_email
            }
          }
        }
        """
        
        variables = {
            "fromDate": from_date,
            "participantEmail": self.user_email
        }
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if 'errors' in data:
                print(f"❌ GraphQL errors: {data['errors']}")
                return []
            
            transcripts = data.get('data', {}).get('transcripts', [])
            return transcripts
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching transcripts: {e}")
            return []
    
    def analyze_transcript_with_claude(self, transcript):
        """Analyze transcript for Dylan-specific action items"""
        if not self.claude_client:
            print("❌ Claude API key not configured")
            return []
        
        try:
            # Extract relevant content from transcript
            title = transcript.get('title', 'Unknown Meeting')
            date = transcript.get('date', '')
            organizer = transcript.get('organizer_email', 'Unknown')
            
            # Get action items from summary if available
            summary_action_items = []
            if transcript.get('summary') and transcript['summary'].get('action_items'):
                summary_action_items = transcript['summary']['action_items']
            
            # Get sentences where Dylan is mentioned or speaking
            dylan_sentences = []
            for sentence in transcript.get('sentences', []):
                text = sentence.get('text', '').lower()
                speaker = sentence.get('speaker_name', '').lower()
                
                # Include if Dylan is speaking or mentioned
                if 'dylan' in text or 'dylan' in speaker:
                    dylan_sentences.append({
                        'speaker': sentence.get('speaker_name', 'Unknown'),
                        'text': sentence.get('text', '')
                    })
            
            # Prepare the prompt
            prompt = f"""
            Analyze this meeting transcript and extract any action items or todos that are specifically assigned to Dylan (me).
            
            Meeting Details:
            Title: {title}
            Date: {date}
            Organizer: {organizer}
            
            Existing Action Items from Summary:
            {json.dumps(summary_action_items, indent=2)}
            
            Dylan-related excerpts from transcript:
            {json.dumps(dylan_sentences[:10], indent=2)}  # Limit to first 10 for token efficiency
            
            Instructions:
            - Only extract action items that Dylan specifically needs to do
            - Look for phrases like "Dylan will...", "Dylan can you...", "@Dylan", etc.
            - it may not explicitly mention Dylan, but if the context implies a task for Dylan, include it
            - Include follow-ups, commitments, or tasks Dylan agreed to
            - Ignore general discussion or questions Dylan asked without commitments
            - Format each todo as a clear, actionable statement
            - Include relevant context or deadlines if mentioned
            - If there are no specific action items for Dylan, respond with "NO_TODOS"
            
            Format your response as a simple list, one todo per line, starting each with "- "
            """
            
            response = self.claude_client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=100000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text.strip()
            
            if result == "NO_TODOS":
                return []
            
            # Parse todos from response
            todos = []
            for line in result.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    todos.append(line[2:].strip())
                elif line and not line.startswith('NO_TODOS'):
                    todos.append(line.strip())
            
            return todos
            
        except Exception as e:
            print(f"❌ Error analyzing transcript with Claude: {e}")
            return []
    
    def check_new_transcripts(self):
        """Check for new transcripts and extract todos"""
        print("🎙️ Checking for new Fireflies transcripts...")
        
        # Get recent transcripts
        transcripts = self.get_recent_transcripts(hours_back=1)
        
        # Filter for new transcripts
        new_transcripts = []
        for transcript in transcripts:
            # Parse the transcript date
            transcript_date_str = transcript.get('date', '')
            if transcript_date_str:
                try:
                    # Try different date formats
                    if transcript_date_str.endswith('Z'):
                        transcript_date = datetime.fromisoformat(transcript_date_str[:-1] + '+00:00')
                    else:
                        transcript_date = datetime.fromisoformat(transcript_date_str)
                    
                    # Only process if newer than last check
                    if transcript_date > self.last_transcript_check:
                        new_transcripts.append(transcript)
                except Exception as e:
                    print(f"⚠️ Error parsing date for transcript {transcript.get('id')}: {e}")
                    # Include it anyway if we can't parse the date
                    new_transcripts.append(transcript)
        
        # Process new transcripts for todos
        if new_transcripts:
            print(f"\n🔔 Found {len(new_transcripts)} new transcript(s):")
            for transcript in new_transcripts:
                print(f"\n--- New Transcript ---")
                print(f"Title: {transcript.get('title', 'Unknown')}")
                print(f"Date: {transcript.get('date', 'Unknown')}")
                print(f"Organizer: {transcript.get('organizer_email', 'Unknown')}")
                
                participants = transcript.get('participants', [])
                if participants:
                    participant_names = [p.get('name', p.get('email', 'Unknown')) for p in participants]
                    print(f"Participants: {', '.join(participant_names[:5])}")  # Limit display
                
                # Analyze with Claude for todos
                print("🤖 Analyzing transcript with Claude...")
                todos = self.analyze_transcript_with_claude(transcript)
                
                if todos:
                    print(f"✅ Found {len(todos)} action item(s) for Dylan:")
                    for todo in todos:
                        print(f"  - {todo}")
                    
                    # Save todos using TodoManager
                    title = transcript.get('title', 'Unknown Meeting')
                    date = transcript.get('date', '')
                    source_info = f"Extracted from Fireflies transcript: {title} [{date}]"
                    self.todo_manager.save_todos_to_file(todos, source_info)
                else:
                    print("ℹ️ No action items found for Dylan")
                    
                print("-" * 50)
        else:
            print("✓ No new transcripts found")
        
        # Update last check time
        self.last_transcript_check = datetime.now(timezone.utc)