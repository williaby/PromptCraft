---
category: function_control
complexity: medium
estimated_time: "< 5 minutes"
dependencies: []
sub_commands: [
  "load-category",
  "unload-category",
  "list-categories",
  "optimize-for",
  "tier-status",
  "save-profile",
  "load-profile",
  "performance-stats",
  "help",
  "analytics"
]
version: "1.0"
---

# Function Loading Control System

Comprehensive user control over dynamic function loading with power user features: $ARGUMENTS

## Overview

The function loading control system gives you granular control over which Claude Code functions are available, optimizing performance while maintaining functionality. This system implements:

- **Conservative Defaults**: Safe function loading that prioritizes functionality
- **User Override Commands**: Direct control when you need specific functions
- **Power User Features**: Advanced optimization and automation capabilities
- **Learning System**: Adaptive improvements based on usage patterns
- **Analytics Engine**: Insights and optimization recommendations

## Command Categories

### Category Management Commands

Control which function categories are loaded:

```bash
# List all available categories and their status
/project:function-loading-control list-categories

# List only loaded categories
/project:function-loading-control list-categories loaded-only

# List categories by tier
/project:function-loading-control list-categories tier:2

# Load a specific category
/project:function-loading-control load-category security

# Unload a category (Tier 2 and 3 only)
/project:function-loading-control unload-category external

# Get detailed information about a category
/project:function-loading-control category-info analysis
```

### Tier Control Commands

Manage function tiers for systematic loading:

```bash
# Show current tier loading status
/project:function-loading-control tier-status

# Force load a specific tier
/project:function-loading-control load-tier 2

# Unload a tier (use --force for Tier 1)
/project:function-loading-control unload-tier 3

# Optimize for specific task types
/project:function-loading-control optimize-for debugging
/project:function-loading-control optimize-for security
/project:function-loading-control optimize-for minimal
```

### Performance Commands

Monitor and optimize system performance:

```bash
# Show function loading statistics
/project:function-loading-control performance-stats

# Clear function loading cache
/project:function-loading-control clear-cache

# Run performance benchmark
/project:function-loading-control benchmark-loading

# Set performance mode
/project:function-loading-control performance-mode aggressive
/project:function-loading-control performance-mode conservative
```

### Session Management Commands

Save and restore function configurations:

```bash
# Save current setup as named profile
/project:function-loading-control save-profile auth-work "Authentication workflow"

# Load previously saved profile
/project:function-loading-control load-profile auth-work

# List all saved profiles
/project:function-loading-control list-profiles

# List profiles with specific tag
/project:function-loading-control list-profiles tag:security

# Enable automatic profile detection
/project:function-loading-control auto-profile on
```

### Help and Analytics Commands

Get help and insights:

```bash
# Comprehensive help system
/project:function-loading-control help
/project:function-loading-control help categories
/project:function-loading-control help optimization

# Usage analytics and insights
/project:function-loading-control analytics

# Show usage recommendations
/project:function-loading-control recommendations
```

## Function Categories and Tiers

### Tier 1: Essential (Always Loaded)
- **core**: Essential operations (Read, Write, Edit, Bash, LS, Glob, Grep)
- **git**: Version control operations (git_status, git_add, git_commit, etc.)
- **Token Cost**: ~9,040 tokens
- **Usage**: 90%+ of sessions

### Tier 2: Extended (Conditional Loading)
- **analysis**: AI analysis tools (chat, thinkdeep, analyze, consensus, debug)
- **quality**: Code improvement (codereview, refactor, docgen, testgen)
- **security**: Security tools (secaudit, precommit)
- **test**: Testing tools (testgen validation)
- **debug**: Debugging tools (debug, tracer)
- **Token Cost**: ~14,940 tokens
- **Usage**: 30-60% of sessions

### Tier 3: Specialized (On-Demand)
- **external**: External services (context7, time, safety)
- **infrastructure**: Resource management (MCP resources)
- **Token Cost**: ~3,850 tokens
- **Usage**: <20% of sessions

## Task Optimization Types

Optimize function loading for specific workflows:

### Development Tasks
- `debugging` - Loads debug, analysis tools for troubleshooting
- `refactoring` - Loads quality, analysis tools for code improvement
- `testing` - Loads test, quality tools for validation
- `documentation` - Loads quality, analysis tools for docs

### Security Tasks
- `security` - Loads security, analysis tools for auditing

### Performance Tasks
- `minimal` - Only essential functions for basic operations
- `comprehensive` - All functions for complex multi-domain tasks

## Usage Patterns and Workflows

### Beginner Workflow
1. Start with default conservative loading
2. Use `/project:function-loading-control help` for guidance
3. Load specific categories as needed: `/project:function-loading-control load-category security`
4. Check status: `/project:function-loading-control tier-status`

### Intermediate Workflow
1. Optimize for your task: `/project:function-loading-control optimize-for debugging`
2. Save useful configurations: `/project:function-loading-control save-profile debug-work`
3. Monitor performance: `/project:function-loading-control performance-stats`
4. Adjust as needed based on usage

### Power User Workflow
1. Use analytics for insights: `/project:function-loading-control analytics`
2. Create task-specific profiles for different workflows
3. Set performance mode based on needs
4. Leverage automatic optimization features

## Performance Considerations

### Token Usage
- **Conservative Mode**: Loads more functions for safety (~20,000 tokens)
- **Balanced Mode**: Optimizes based on task detection (~15,000 tokens)
- **Aggressive Mode**: Minimal loading for performance (~12,000 tokens)

### Response Time Impact
- Each loaded category adds ~10-50ms to response time
- Cache hit rates significantly improve repeated operations
- Task-specific optimization reduces overhead by 40-70%

### Memory Usage
- System tracks usage patterns for optimization
- Cache intelligently manages function metadata
- Background analytics provide continuous improvement

## Advanced Features

### Learning and Adaptation
- System learns from your usage patterns
- Provides personalized optimization recommendations
- Adapts thresholds based on user behavior
- Suggests workflow improvements

### Analytics and Insights
- Tracks command usage and patterns
- Identifies optimization opportunities
- Provides efficiency scoring
- Generates actionable recommendations

### Integration with Existing Workflows
- Works seamlessly with existing Claude Code commands
- Maintains compatibility with project workflows
- Provides context-aware suggestions
- Integrates with help system for guidance

## Safety and Fallback

### Conservative Defaults
- Tier 1 functions always loaded for basic operation
- Fallback chains prevent functionality loss
- Error recovery with suggested actions
- Graceful degradation when needed

### Validation and Confirmation
- Prevents destructive operations without confirmation
- Validates commands before execution
- Provides clear feedback and suggestions
- Tracks errors for system improvement

## Examples and Common Scenarios

### Daily Development Workflow
```bash
# Start your day - check what's loaded
/project:function-loading-control tier-status

# Working on authentication feature
/project:function-loading-control optimize-for security
/project:function-loading-control load-category analysis

# Save this setup for future auth work
/project:function-loading-control save-profile auth-development "Security and analysis tools for auth"

# Check performance impact
/project:function-loading-control performance-stats
```

### Debugging Session
```bash
# Optimize for debugging
/project:function-loading-control optimize-for debugging

# Load additional analysis tools if needed
/project:function-loading-control load-category analysis

# Monitor usage during debugging
/project:function-loading-control performance-stats

# Save successful debugging setup
/project:function-loading-control save-profile debug-session "Debugging workflow with analysis"
```

### Performance Optimization
```bash
# Check current analytics
/project:function-loading-control analytics

# Switch to aggressive mode for routine tasks
/project:function-loading-control performance-mode aggressive

# Load only what's needed
/project:function-loading-control optimize-for minimal

# Monitor improvement
/project:function-loading-control benchmark-loading
```

### Learning and Improvement
```bash
# Get usage insights
/project:function-loading-control analytics

# See what can be optimized
/project:function-loading-control recommendations

# Learn about advanced features
/project:function-loading-control help optimization

# Track progress over time
/project:function-loading-control performance-stats
```

## Troubleshooting

### Common Issues

**"Unknown category: xyz"**
- Check available categories: `/project:function-loading-control list-categories`
- Use exact category names (case-sensitive)
- Try category info: `/project:function-loading-control category-info <name>`

**"Cannot unload category 'core'"**
- Core and git categories are always loaded for safety
- Focus on managing Tier 2 and 3 categories
- Use task optimization instead of manual management

**Performance Issues**
- Check loaded categories: `/project:function-loading-control list-categories loaded-only`
- Clear cache: `/project:function-loading-control clear-cache`
- Switch to aggressive mode: `/project:function-loading-control performance-mode aggressive`

**Profile Issues**
- List available profiles: `/project:function-loading-control list-profiles`
- Check spelling and case sensitivity
- Profiles are saved locally and persist across sessions

### Getting Help

- General help: `/project:function-loading-control help`
- Command-specific help: `/project:function-loading-control help <topic>`
- Context-aware suggestions based on recent activity
- Progressive learning paths for mastering features

## Integration Notes

This command integrates with:
- **Task Detection System**: Automatic function loading based on query analysis
- **Performance Monitor**: Real-time optimization and caching
- **Analytics Engine**: Usage tracking and pattern recognition
- **Help System**: Context-aware guidance and learning paths
- **Profile System**: Configuration persistence and sharing

## Best Practices

1. **Start Conservative**: Use default loading and optimize as needed
2. **Task-Specific Optimization**: Use optimize-for commands for focused work
3. **Profile Management**: Save useful configurations for repeated workflows
4. **Monitor Performance**: Regular check of stats and analytics
5. **Learn Incrementally**: Use help system to gradually master features
6. **Share Insights**: Export analytics for team optimization

---

*This comprehensive function loading control system empowers users while maintaining Claude Code's conservative defaults and ensuring system reliability.*
