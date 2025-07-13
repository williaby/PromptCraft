# PushCut Notification Command

Send a notification to your phone via PushCut webhook when Claude finishes responding.

## Usage

```bash
/notification [message] [priority] [url]
```

## Arguments

- `message` (optional): Custom notification message. Default: "Claude has completed your request"
- `priority` (optional): Notification priority level (low, normal, high, critical). Default: normal
- `url` (optional): PushCut webhook URL. Uses environment variable if not provided

## Implementation

```bash
# Set your PushCut webhook URL as environment variable (recommended)
export PUSHCUT_WEBHOOK_URL="https://api.pushcut.io/webhook/YOUR_WEBHOOK_ID"

# Basic notification
curl -X POST "$PUSHCUT_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Claude Code",
    "text": "$ARGUMENTS",
    "isTimeSensitive": true,
    "badge": 1
  }'

# Enhanced notification with metadata
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
WORKING_DIR=$(basename "$PWD")

curl -X POST "$PUSHCUT_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Claude Code - '$WORKING_DIR'",
    "text": "'"${1:-Claude has completed your request}"'",
    "subtitle": "'"$TIMESTAMP"'",
    "isTimeSensitive": true,
    "badge": 1,
    "sound": "'"${2:-default}"'",
    "url": "'"${3:-}"'"
  }'
```

## Advanced Features

### Priority-Based Notifications

```bash
case "${2:-normal}" in
  "low")
    SOUND="none"
    TIME_SENSITIVE="false"
    ;;
  "normal")
    SOUND="default"
    TIME_SENSITIVE="false"
    ;;
  "high")
    SOUND="alert"
    TIME_SENSITIVE="true"
    ;;
  "critical")
    SOUND="alarm"
    TIME_SENSITIVE="true"
    ;;
esac
```

### Context-Aware Notifications

```bash
# Detect current git branch and include in notification
BRANCH=$(git branch --show-current 2>/dev/null || echo "no-git")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "")

# Include system resource usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')

curl -X POST "$PUSHCUT_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Claude Code - '$WORKING_DIR'",
    "text": "'"${1:-Task completed}"'",
    "subtitle": "Branch: '$BRANCH' | CPU: '$CPU_USAGE'% | Mem: '$MEMORY_USAGE'%",
    "isTimeSensitive": '$TIME_SENSITIVE',
    "badge": 1,
    "sound": "'$SOUND'",
    "url": "'"${3:-}"'"
  }'
```

## Environment Setup

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# PushCut Configuration
export PUSHCUT_WEBHOOK_URL="https://api.pushcut.io/webhook/YOUR_WEBHOOK_ID"
export PUSHCUT_DEFAULT_SOUND="default"
export PUSHCUT_DEFAULT_PRIORITY="normal"
```

## Error Handling

```bash
# Validate webhook URL exists
if [ -z "$PUSHCUT_WEBHOOK_URL" ] && [ -z "$3" ]; then
  echo "Error: PushCut webhook URL not configured. Set PUSHCUT_WEBHOOK_URL environment variable or provide as third argument."
  exit 1
fi

# Silent failure option for offline scenarios
WEBHOOK_URL="${3:-$PUSHCUT_WEBHOOK_URL}"
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{...}' \
  --max-time 5 \
  --silent \
  --fail \
  || echo "Warning: Failed to send notification (offline or webhook unreachable)"
```

## Integration Examples

### With Long-Running Tasks

```bash
# Notify when tests complete
/notification "Test suite completed" "high" && poetry run pytest

# Notify after code generation
/notification "Code generation finished - review required" "normal"

# Notify on deployment completion
/notification "Deployment to staging complete" "high" "https://staging.yourapp.com"
```

### Conditional Notifications

```bash
# Only notify on failures
if ! poetry run pytest; then
  /notification "Tests failed - attention required" "critical"
fi

# Notify based on time of day
HOUR=$(date +%H)
if [ $HOUR -lt 9 ] || [ $HOUR -gt 17 ]; then
  /notification "After-hours task completed" "normal"
fi
```

## Security Considerations

- Store webhook URLs in environment variables, not in command history
- Use HTTPS webhooks only
- Consider webhook URL rotation for sensitive projects
- Avoid including sensitive information in notification text

## PushCut App Configuration

To maximize effectiveness:

1. Create a dedicated "Claude Code" notification in PushCut app
2. Configure custom sounds for different priorities
3. Set up automation rules based on notification content
4. Enable widget shortcuts for quick access to common responses
