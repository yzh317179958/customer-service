# Intent Recognition Prompt

> **Version**: v3.1
> **Updated**: 2025-12-29
> **Code Version**: v7.8.0

Analyze user input, determine intent type, and extract key entity information.

**Note**: `contact_agent` (Contact support team) is handled directly by the backend, not through Coze workflow.

---

## 1. Input Variables

| Variable | Description | Source |
|----------|-------------|--------|
| `{{user_input}}` | User's question | User message |
| `{{chat_history}}` | Chat history | Session context |
| `{{INTENT}}` | Frontend pre-passed intent (optional) | API parameters |

---

## 2. Intent Classification Overview

### Frontend Quick Button INTENT (3 types)

| INTENT Value | Description | Button Clicked |
|--------------|-------------|----------------|
| `presale` | Pre-sales inquiry | Pre-sales inquiry |
| `tracking` | Package tracking | Where's my package? |
| `after_sale` | After-sales support | After-sales support |

### Coze Internal intent (6 types)

| intent | Description | Routes To |
|--------|-------------|-----------|
| `presale` | Pre-sales (product, price, recommendation) | Pre-sales Reply |
| `tracking` | Package tracking (has order number) | Order Query Reply |
| `order_list` | Email order lookup (has email, no order number) | Email Query Reply |
| `order_guide` | Order guidance (no order number, no email) | Order Guide Reply |
| `after_sale` | After-sales issues | After-sales Reply |
| `general_chat` | Casual chat/greetings | General Reply |

> ⚠️ Frontend only passes 3 INTENTs, but Coze internal recognition can output 6 intent types

---

## 3. Intent Judgment Flow

**Step 1: Check if frontend passed INTENT parameter**

If INTENT has value, process according to these rules:

| Frontend INTENT | Processing Logic |
|-----------------|------------------|
| `presale` | Output `intent: presale` directly |
| `tracking` | Further determine based on user input:<br>• Has order number → `tracking`<br>• Has email, no order number → `order_list`<br>• Neither → `order_guide` |
| `after_sale` | Output `intent: after_sale` directly |

If INTENT is empty, proceed to Step 2.

**Step 2: Analyze user input to identify intent**

Judge by priority:

1. User message contains order number → `tracking`
2. User message contains email and mentions order → `order_list`
3. User mentions checking order/tracking but no order number or email → `order_guide`
4. Involves return, exchange, repair, complaint keywords → `after_sale`
5. Involves product inquiry, price, recommendation → `presale`
6. Casual chat/greetings (Hi, Thanks, Hello) → `general_chat`

**Step 3: Extract entity information**

Extract order number and email from user input (if any).

---

## 4. Intent Classification Details

### 1. presale (Pre-sales Inquiry)

**Trigger**: User inquires about Fiido products

**Keywords**:
- Product: specs, range, price, how much, recommend, which one, compare, difference
- Purchase: order, payment, shipping time, availability, discount
- Usage: how to use, riding, maintenance

**Examples**:
- "What's the range of C11 Pro"
- "Which bike is good for commuting"
- "Any promotions available"

### 2. tracking (Package Tracking)

**Trigger**: User provides order number, wants to check order status or tracking

**Keywords**: order number, check order, tracking, shipping, where is, order status

**Order Number Format**:
- Prefix: UK, EU, DE, FR, IT, ES, NL, PL, US, AU, CA, JP (case insensitive)
- Variants: #UK22080, UK-22080, uk22080
- Extraction: Remove # and -, convert to uppercase

**Examples**:
- "Check order UK22080"
- "Has NL16479 shipped"
- "Where is my order DE10090"

### 3. order_list (Email Order Lookup)

**Trigger**: User provides email but no order number, wants to check order list

**Keywords**: my orders, order history, email

**Examples**:
- "My email is xxx@gmail.com, check my orders"
- "I ordered with xxx@gmail.com"

### 4. order_guide (Order Guidance)

**Trigger**: User wants to check order but provides no order number or email

**Keywords**: check order, order status, tracking (but no specific info)

**Examples**:
- "I want to check my order"
- "How to track shipping"
- "Where is my order" (no order number)

### 5. after_sale (After-sales Support)

**Trigger**: User has purchased product, needs after-sales support

**Keywords**:
- Return/Refund: return, refund
- Exchange: exchange, replace
- Repair: repair, broken, not working
- Complaint: complaint, unsatisfied
- Warranty: warranty

**Examples**:
- "I want to return"
- "Battery is broken"
- "How to apply for exchange"

### 6. general_chat (Casual Chat)

**Trigger**: User engages in casual chat, greetings, or unrelated conversation

**Keywords**: Hi, Hello, Thanks, Thank you, Bye, Goodbye

**Examples**:
- "Hello"
- "Thanks"
- "Hi there"

---

## 5. Entity Extraction Rules

### Order Number (order_number)
- Format: Country/region code + numbers
- Supported prefixes: UK, EU, DE, FR, IT, ES, NL, PL, US, AU, CA, JP
- Variant handling: Remove # and -, convert to uppercase
- Examples: UK22080, NL16479, DE10090

### Email (email)
- Standard email format: xxx@xxx.com
- Recognize email in user's message

---

## 6. Output Format

Output JSON object directly, without code block:

{
  "intent": "tracking",
  "order_number": "UK22080",
  "email": null,
  "confidence": 0.95,
  "reason": "User provided order number UK22080, wants tracking status",
  "from_intent_param": false
}

**Field Descriptions**:
| Field | Description |
|-------|-------------|
| `intent` | Intent: presale / tracking / order_list / order_guide / after_sale / general_chat |
| `order_number` | Extracted order number, null if none |
| `email` | Extracted email, null if none |
| `confidence` | Confidence 0-1 |
| `reason` | Judgment reason (brief) |
| `from_intent_param` | Whether from frontend INTENT parameter (true/false) |

---

## 7. INTENT Parameter Processing Rules

### presale
Direct mapping:
```
INTENT=presale → intent=presale
```

### tracking
Further judgment needed:
```
INTENT=tracking + has order number → intent=tracking
INTENT=tracking + has email, no order number → intent=order_list
INTENT=tracking + neither → intent=order_guide
```

### after_sale
Direct mapping:
```
INTENT=after_sale → intent=after_sale
```

---

## 8. Judgment Priority

1. **Highest**: Frontend INTENT (but tracking needs further judgment)
2. **High**: User message has order number → tracking
3. **Medium**: Has email and mentions order → order_list
4. **Medium**: Mentions order but no info → order_guide
5. **Medium**: After-sales keywords → after_sale
6. **Medium**: Product-related → presale
7. **Fallback**: Casual chat → general_chat

---

## 9. Examples

### Example 1: Frontend passes tracking + user provides order number
**Input**:
- INTENT = tracking
- user_input = "Has UK22080 shipped"

**Output**:
{
  "intent": "tracking",
  "order_number": "UK22080",
  "email": null,
  "confidence": 1.0,
  "reason": "Frontend passed tracking, extracted order number UK22080",
  "from_intent_param": true
}

### Example 2: Frontend passes tracking + user provides email
**Input**:
- INTENT = tracking
- user_input = "My email is test@gmail.com"

**Output**:
{
  "intent": "order_list",
  "order_number": null,
  "email": "test@gmail.com",
  "confidence": 1.0,
  "reason": "Frontend passed tracking, user provided email, route to email lookup",
  "from_intent_param": true
}

### Example 3: Frontend passes tracking + no order number or email
**Input**:
- INTENT = tracking
- user_input = "Help me check"

**Output**:
{
  "intent": "order_guide",
  "order_number": null,
  "email": null,
  "confidence": 1.0,
  "reason": "Frontend passed tracking, but user provided no order number or email, needs guidance",
  "from_intent_param": true
}

### Example 4: No INTENT + casual chat
**Input**:
- INTENT = (empty)
- user_input = "Hello"

**Output**:
{
  "intent": "general_chat",
  "order_number": null,
  "email": null,
  "confidence": 0.9,
  "reason": "User greeting, recognized as casual chat",
  "from_intent_param": false
}

### Example 5: No INTENT + after-sales
**Input**:
- INTENT = (empty)
- user_input = "I want to return, order number UK22081"

**Output**:
{
  "intent": "after_sale",
  "order_number": "UK22081",
  "email": null,
  "confidence": 0.95,
  "reason": "User clearly states return intent with order number",
  "from_intent_param": false
}

---

## 10. User Input

{{user_input}}

## 11. Chat History (if any)

{{chat_history}}

## 12. Frontend Pre-passed Parameter (if any)

INTENT: {{INTENT}}

---

## 13. Version History

### v3.1 (2025-12-29)
- **Restored full branches**: Kept order_list, order_guide, general_chat
- **Clarified frontend vs internal branches**:
  - Frontend INTENT: presale / tracking / after_sale (3)
  - Internal intent: presale / tracking / order_list / order_guide / after_sale / general_chat (6)
- **Enhanced tracking logic**: Further determine routing based on user input

### v3.0 (2025-12-29)
- Simplified frontend INTENT to three business branches

### v2.2 (2025-12-25)
- Simplified flow description

### v1.0 (2025-12-10)
- Initial version
