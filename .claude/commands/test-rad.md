---
description: Test the Response-Aware Development system with sample assumptions
argument-hint: [test-type]
allowed-tools: Bash(echo:*), Read, Write
---

# Test RAD System

Test the Response-Aware Development system by creating sample assumption tags and verifying the workflow.

## Task

Create sample code with assumption tags and demonstrate the RAD verification process.

Test type from arguments: `$ARGUMENTS` (defaults to "basic" if empty)

## Implementation

### 1. Create Test File with Sample Assumptions

```javascript
// test-assumptions.js - Generated for RAD testing

// #CRITICAL: payment: Payment gateway assumed to respond within 5 seconds
// #VERIFY: Add timeout handler and retry logic with exponential backoff
function processPayment(amount) {
    return paymentGateway.charge(amount);
}

// #ASSUME: state: User authentication state persists across page refreshes
// #VERIFY: Add token validation and refresh logic
function getCurrentUser() {
    return localStorage.getItem('currentUser');
}

// #EDGE: browser: Clipboard API availability assumed across all browsers
// #VERIFY: Add fallback for unsupported browsers using document.execCommand
function copyToClipboard(text) {
    return navigator.clipboard.writeText(text);
}

// #CRITICAL: concurrency: Database transaction isolation assumed for concurrent updates
// #VERIFY: Add explicit transaction locks and conflict resolution
async function updateUserBalance(userId, amount) {
    const user = await db.users.findById(userId);
    user.balance += amount;
    return user.save();
}

// #ASSUME: timing: State update completion assumed before navigation
// #VERIFY: Use callback or state confirmation before routing
function updateProfile(userData) {
    setUserData(userData);
    navigateToProfile(userData.id);
}
```

### 2. Demonstrate Assumption Detection

Use Bash to find the assumptions:

```bash
echo "=== RAD Test Results ==="
echo ""
echo "Critical Assumptions Found:"
grep -n "#CRITICAL:" test-assumptions.js || echo "None found"
echo ""
echo "Standard Assumptions Found:"  
grep -n "#ASSUME:" test-assumptions.js || echo "None found"
echo ""
echo "Edge Case Assumptions Found:"
grep -n "#EDGE:" test-assumptions.js || echo "None found"
```

### 3. Show Verification Command Usage

```bash
echo ""
echo "=== Next Steps ==="
echo "1. Run verification command:"
echo "   /verify-assumptions-smart --scope=current-file"
echo ""
echo "2. For critical only:"
echo "   /verify-assumptions-smart --strategy=critical-only"  
echo ""
echo "3. List all assumptions:"
echo "   /list-assumptions"
```

### 4. Demonstrate Model Selection Logic

Explain which models would be used:

- **Line 3 (payment)**: Gemini 2.5 Pro or O3-Mini (critical payment logic)
- **Line 8 (auth state)**: DeepSeek-R1 via dynamic selection (state management)
- **Line 13 (clipboard)**: Gemini Flash Lite (edge case browser compatibility)  
- **Line 18 (concurrency)**: Gemini 2.5 Pro (critical database consistency)
- **Line 25 (timing)**: Qwen-Coder via dynamic selection (React/state patterns)

### 5. Clean Up Test File

```bash
echo ""
echo "=== Cleanup ==="
echo "Test file created: test-assumptions.js"
echo "Remove with: rm test-assumptions.js"
echo ""
echo "RAD system test complete!"
```

This test demonstrates:

1. ✅ Assumption tagging methodology
2. ✅ Risk-based categorization
3. ✅ Model selection logic
4. ✅ Integration with verification workflow
5. ✅ Command-line interface
