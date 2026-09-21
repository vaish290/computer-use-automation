# Computer Use Automation — Design Report

## 1. Overview

The main idea behind this project is to separate **learning a workflow** from **repeating that workflow**.

During the first run, the system uses an LLM to understand the web page and figure out what actions are needed. It observes the page, decides one action at a time, performs the action, and records what worked.

Once the workflow is completed successfully, those recorded actions are converted into a structured workflow artifact.

After that, the system does not need the LLM to perform the same workflow again. Replay simply loads the saved artifact and executes the recorded steps using Playwright.

The overall flow looks like this:

```text
Goal
  ↓
LLM Discovery
  ↓
Recorded Steps
  ↓
Workflow Artifact
  ↓
Deterministic Replay
  ↓
Result + Evidence
```

The main reason for this design is predictability. The LLM is useful when the system needs to understand an unfamiliar interface, but repeatedly asking the model to reason through the same workflow would make execution less predictable.

Instead, the LLM is used during discovery, while replay follows the stored workflow.

---

## 2. Architecture

The system has three main parts:

```text
User Goal
   │
   ▼
Discovery
Observe → LLM Decide → Safety Check → Act → Record
   │
   ▼
Workflow Artifact
Inputs → Steps → Locators → Outputs → Outcomes → Checkpoint
   │
   ▼
Deterministic Replay
Validate Input → URL Safety → Resolve Locator → Action Safety
→ Execute → Read Output → Check Outcome → Verify Checkpoint
   │
   ▼
Structured Result + Evidence
```

### Why is the LLM only used during discovery?

The LLM is useful when the system needs to understand what is currently available on a page and decide what to do next.

Once that workflow has already been discovered, there is no need for the model to make the same decisions every time.

Replay therefore does not ask the LLM what action to perform. It simply follows the steps stored in the artifact.

This also makes replay much easier to test because the same artifact should result in the same sequence of actions.

### Why use an artifact?

The artifact acts as the connection between discovery and replay.

Discovery creates it, and replay uses it.

The replay system does not need the original LLM conversation or reasoning. Everything needed to repeat the workflow is stored in the artifact.

The current prototype intentionally supports a small set of UI elements and actions. The observer mainly understands inputs, buttons, page text, and simple two-column tables, while replay supports `fill`, `click`, and `read`.

I kept the scope small so that the full discovery-to-replay flow could be implemented and tested properly instead of partially supporting many different browser actions.

---

## 3. Artifact Schema

Workflow artifacts are validated using Pydantic.

The current schema version is:

```text
1.1
```

An artifact contains:

* workflow name and description
* target URL
* runtime inputs
* ordered workflow steps
* primary and fallback locators
* expected outputs
* business outcomes
* final success checkpoint

For example, a workflow may define:

```text
input:
member_id

steps:
fill member number
click search
read savings balance

output:
savings_balance
```

### Locator fallbacks

Instead of storing only one selector for an element, the artifact can store a primary locator and fallback locators.

Supported locator strategies include:

```text
id
name
label
role
css
```

During replay, the system first tries the primary locator.

If that locator does not identify exactly one visible element, replay tries the fallback locators.

Only when none of them work does the step fail.

This makes the workflow less dependent on a single selector.

### Runtime parameters

The workflow should also work with values other than the one originally used during discovery.

For example, discovery may use:

```text
12345
```

When the artifact is created, that value becomes:

```text
{{member_id}}
```

Later, replay can run the same workflow using:

```text
67890
```

without running discovery again.

If the required input is missing, replay raises a clear error such as:

```text
Missing required input: member_id
```

### Current locator limitation

The current implementation supports `role` and `label` locators, but DOM-based locators such as `id` and `name` may still be tried first.

Because of that, the current system is not fully accessibility-tree-first.

A future improvement would be to prioritize `role`, accessible name, and label before DOM-specific selectors.

---

## 4. Deterministic Replay and Error Handling

Replay does not ask the LLM what to do.

It loads the artifact and executes the steps in the stored order.

The basic replay flow is:

```text
Load Artifact
      ↓
Validate Input
      ↓
Check Target URL
      ↓
Open Application
      ↓
Check Action Safety
      ↓
Resolve Locator
      ↓
Execute Step
      ↓
Check Business Outcome
      ↓
Read Output
      ↓
Verify Checkpoint
```

The system keeps different types of results separate.

| Result             | Meaning                                                                |
| ------------------ | ---------------------------------------------------------------------- |
| `success`          | Workflow completed and the checkpoint passed                           |
| `business_outcome` | The application returned an expected result such as `member_not_found` |
| `blocked`          | The safety policy stopped the navigation or action                     |
| `failure`          | A technical problem occurred                                           |

For example, if the user searches for a member who does not exist, the website may correctly display:

```text
Member not found
```

That does not mean Playwright failed.

The system therefore returns something like:

```text
status = business_outcome
code = member_not_found
```

A technical failure is different. Examples include:

* no stored locator can find the element
* a browser step fails
* navigation fails
* the final checkpoint is missing

### Retry limitation

Automatic retry or backoff for temporary failures is not currently implemented.

For example, if a page is temporarily slow and a step times out, the current implementation may return a technical failure instead of automatically retrying it.

This would be an important improvement for a production system.

---

## 5. Multi-Tenant Support

The same automation engine is demonstrated with two different tenant interfaces.

### Tenant A

```text
Input: member_id
Button: Search Member
Result: Savings Balance
```

Example:

```text
12345 → $4,320.50
```

### Tenant B

```text
Input: customer_id
Button: Find Customer
Result: Savings Amount
```

Example:

```text
C1001 → $8,120.75
```

The two interfaces use different:

* URLs
* input names
* labels
* button names
* result terminology

However, the core discovery and replay code is the same.

Tenant-specific information is stored in configuration, including:

* target URL
* input name
* goal
* artifact path
* checkpoint
* business outcomes

This means I do not need a completely separate replay implementation for every tenant.

The configuration and artifact describe what is different, while the main automation engine stays reusable.

### Supporting other interfaces

The project also includes a surface abstraction.

The idea is that page observation should not have to be permanently tied to one type of interface.

For example, a legacy website may depend more heavily on accessible labels and roles because it may not have clean IDs.

A desktop application could eventually use operating-system accessibility APIs instead of Playwright.

The current project does not implement desktop automation, but the separation provides a place where another surface implementation could be added later.

---

## 6. Human Takeover

Some actions should not be performed automatically.

Examples include actions related to:

```text
transfer
payment
submit
confirm
```

When replay detects one of these actions, it returns a `human_required` safety decision.

The important part is that the existing browser session is preserved.

The flow is:

1. Replay pauses.
2. The same Playwright browser remains open.
3. The user can see the current page.
4. Existing cookies, login state, and page state remain available.
5. The user performs the sensitive action manually.
6. The user presses Enter in the terminal.
7. Replay continues from the same session.

Replay does not automatically perform the sensitive action again after the user completes it.

This allows automation to handle normal steps while still giving control back to a person when a sensitive decision or action is reached.

The terminal prompt is only a simple prototype interface.

In a production system, the same idea could be implemented using an operator dashboard or intervention queue.

---

## 7. Safety

The project has two main safety layers:

```text
URL Safety
+
Action Safety
```

### URL and route safety

Before the configured target is opened, the system checks whether its origin and route are allowed.

Allowed origins currently include:

```text
http://127.0.0.1:5000
http://localhost:5000
```

Allowed route prefixes include:

```text
/
/member
/tenant-b
```

For example:

```text
http://127.0.0.1:5000/tenant-b
```

is allowed.

But:

```text
https://example.com
```

is blocked because the origin is not part of the allowlist.

Similarly:

```text
http://127.0.0.1:5000/admin
```

is blocked because `/admin` is not an approved route.

The URL safety check is used by both discovery and replay.

### Action safety

The system also controls which browser actions can be executed automatically.

Currently allowed actions are:

```text
fill
click
read
```

An unsupported action is blocked.

The target name is also checked for sensitive operations.

Examples of blocked terms are:

```text
delete
remove
close account
```

These actions are not executed.

Other actions require a person to take control.

Examples include:

```text
transfer
payment
submit
confirm
```

These are sent through the human takeover flow instead.

### Current safety limitations

The URL allowlist is checked before the configured initial navigation.

The current prototype does not re-check the allowlist after every possible redirect or later navigation.

The keyword-based safety rules are also intentionally simple. Checking words such as `delete` or `payment` is useful for the prototype, but a real system would need a more complete policy model.

The project also does not store credentials inside workflow artifacts or evidence files.

The Groq API key is stored in `.env`, which is excluded from Git.

---

## 8. Evidence and Logging

Both discovery and replay create structured JSON evidence.

The evidence records events such as:

```text
discovery_started
llm_decision
url_safety_check
navigation_started
navigation_completed
safety_check
action_executed
action_recorded
step_started
step_completed
output_extracted
business_outcome
action_blocked
checkpoint_checked
step_failed
replay_completed
```

This makes it easier to understand what happened during a run.

Instead of only seeing:

```text
Workflow failed
```

the evidence can show:

```text
which step was running
what action was attempted
what safety decision was made
what output was extracted
where the workflow failed
what final result was returned
```

This is useful for debugging and also makes the automation easier to review.

---

## 9. Testing

The project includes automated tests for three main areas:

```text
artifact behavior
replay behavior
safety behavior
```

The complete test suite can be run using:

```bash
python -m pytest tests -v
```

The final verified result is:

```text
22 passed
```

### Replay tests

Replay tests cover:

* runtime parameter resolution
* using different runtime values
* keeping normal strings unchanged
* keeping non-string values unchanged
* detecting missing runtime inputs

### Safety tests

Safety tests cover:

* allowing normal actions
* allowing read operations
* blocking destructive actions
* blocking unsupported action types
* requiring human interaction for payment-related actions
* allowing the Tenant A URL
* allowing the Tenant B URL
* blocking an external origin
* blocking an unapproved route

These tests verify the deterministic parts of the system without requiring an LLM for every test run.

---

## 10. What I Intentionally Left Out

Because this is a prototype, I focused on completing the main workflow instead of trying to build every possible browser automation feature.

### Automatic retry

The current system does not automatically retry temporary failures such as a slow page or timeout.

A future version could retry recoverable failures a small number of times before returning an error.

### Accessibility-first locators

The system supports `role` and `label`, but these are not always prioritized ahead of `id` and `name`.

A future version should prefer semantic and accessibility-based locators first.

### Screenshots and recordings

The project currently stores structured JSON evidence.

Screenshots or browser recordings would make debugging easier but are not part of the current implementation.

### Full navigation enforcement

The URL allowlist protects the configured initial target.

A stronger implementation would also check later navigations and redirects.

### Production multi-tenancy

The current tenant configuration is enough to demonstrate the design.

A real multi-tenant system would additionally require:

* authentication
* authorization
* credential isolation
* tenant data isolation
* persistent configuration
* secrets management

### Operator interface

Human takeover currently uses the terminal.

A real system could send an intervention request to an operator dashboard containing information such as:

```text
workflow
current step
reason for takeover
current page
screenshot
```

The operator could complete the action and then return control to automation.

---

## 11. What I Would Build Next

If I had more time, the first improvements I would make are:

1. **Accessibility-first locators**

   I would prioritize `role`, accessible name, and label before DOM-specific selectors such as `id` and CSS.

2. **Retry for temporary failures**

   I would add a small bounded retry mechanism for recoverable browser errors such as timeouts or slow page loads.

3. **Better human handoff**

   I would replace the terminal prompt with an intervention API or operator interface.

4. **Stronger navigation safety**

   I would apply the URL and route safety policy to redirects and later navigations, not only the configured starting URL.

5. **Richer evidence**

   I would add screenshots or browser recordings for important failures and human handoff events.

---

## 12. Final Design Summary

The main design choice in this project is simple:

> **Use the LLM to learn the workflow once, then use deterministic automation to repeat it.**

Discovery provides flexibility because the LLM can inspect an unfamiliar interface and decide what actions are needed.

The artifact makes the discovered workflow reusable by storing the inputs, steps, locators, outputs, business outcomes, and checkpoint.

Replay provides predictability because it follows those stored steps instead of asking the LLM to reason through the workflow again.

Safety adds boundaries around where the automation can navigate and what actions it can perform.

Human takeover allows sensitive actions to stay under human control without losing the existing browser session.

Evidence logging makes each run easier to inspect and debug.

Finally, tenant-specific configuration allows the same core discovery and replay engines to work with different interfaces without creating separate automation code for each tenant.

The current implementation is intentionally a prototype, but it demonstrates the complete path from:

```text
Discovery
   ↓
Reusable Artifact
   ↓
Safe Deterministic Replay
   ↓
Structured Result
```
