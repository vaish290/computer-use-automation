# Computer Use Automation

A browser automation prototype that uses an LLM during **discovery** to understand and complete a workflow, records the successful actions as a reusable artifact, and later executes that artifact through **deterministic replay without using the LLM**.

The project demonstrates reusable browser automation, typed workflow artifacts, locator fallbacks, runtime parameters, structured outputs, URL and action safety checks, human takeover, business outcomes, evidence logging, automated testing, and multi-tenant support across different user interfaces.

---

## 1. Overview

Traditional browser automation usually requires the workflow to be manually coded in advance.

This project separates automation into two phases:

### Discovery

During discovery, the system uses an LLM to determine how to complete a goal on a web application.

The discovery loop follows:

**Observe → Decide → Safety Check → Act → Record**

The system:

1. Validates the configured target URL against the safety allowlist.
2. Opens the target application using Playwright.
3. Observes the available inputs, buttons, page text, and readable data.
4. Sends the current observation, user goal, and previous actions to the LLM.
5. Receives one structured action such as `fill`, `click`, `read`, or `complete`.
6. Checks whether the action is allowed by the safety policy.
7. Executes the action.
8. Records the successful action.
9. Repeats until the goal is complete.
10. Converts the recorded actions into a reusable, versioned artifact.

### Deterministic Replay

Once discovery creates an artifact, the same workflow can be executed again without asking the LLM what to do.

Replay:

1. Loads the saved artifact.
2. Validates required runtime inputs.
3. Checks the configured target URL against the safety allowlist.
4. Opens the target application.
5. Resolves each target using stored locator strategies.
6. Substitutes runtime inputs into parameterized values.
7. Checks each action against the action safety policy.
8. Performs each recorded action in order.
9. Extracts declared outputs.
10. Checks business outcomes and the final success checkpoint.
11. Saves structured evidence for the run.

This keeps the flexible reasoning of an LLM in the discovery phase while making repeated execution predictable.

---

## 2. Example Workflow

The demo application contains a simple savings lookup workflow.

For Tenant A, the user can search using a member number.

Example:

```text
Member Number: 12345
```

The workflow returns:

```text
Savings Balance: $4,320.50
```

During discovery, the system may determine the following actions:

```text
Fill Member Number
        ↓
Click Search Member
        ↓
Read Savings Balance
        ↓
Complete
```

These actions are recorded and converted into a reusable artifact.

Instead of storing:

```text
12345
```

the generated artifact parameterizes the value as:

```text
{{member_id}}
```

The artifact can therefore be replayed with another member ID without running discovery again.

---

## 3. Architecture

The project is organized around two main execution paths.

```text
                    ┌─────────────────────┐
                    │      User Goal      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Discovery      │
                    │                     │
                    │ Observe             │
                    │ Decide with LLM     │
                    │ Safety Check        │
                    │ Execute             │
                    │ Record              │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Versioned Artifact  │
                    │                     │
                    │ Inputs              │
                    │ Steps               │
                    │ Locators            │
                    │ Outputs             │
                    │ Outcomes            │
                    │ Checkpoint          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Deterministic Replay│
                    │                     │
                    │ Load Artifact       │
                    │ Validate Inputs     │
                    │ URL Safety Check    │
                    │ Resolve Locators    │
                    │ Action Safety Check │
                    │ Execute Steps       │
                    │ Extract Outputs     │
                    │ Verify Checkpoint   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Structured Result   │
                    │ + Evidence Log      │
                    └─────────────────────┘
```

---

## 4. Discovery

Discovery is implemented as an iterative **Observe → Decide → Act** loop.

### Observe

The observer inspects the current page and creates a structured representation containing:

* current URL
* page title
* page text
* input controls
* button controls
* readable table data

Controls receive temporary discovery identifiers such as:

```text
control_1
control_2
```

Readable data receives identifiers such as:

```text
data_1
data_2
```

The LLM therefore reasons over structured page information instead of directly generating browser selectors.

### Decide

The planner sends the following information to Groq:

* user goal
* interactive controls
* readable data
* page text
* previous actions

The current planner uses:

```text
openai/gpt-oss-20b
```

The LLM must return exactly one JSON action at a time.

Supported discovery decisions are:

```text
fill
click
read
complete
```

For example:

```json
{
    "action": "fill",
    "target": "control_1",
    "value": "12345"
}
```

or:

```json
{
    "action": "read",
    "target": "data_1",
    "save_as": "savings_balance"
}
```

`complete` is used only after the required information has been read.

---

## 5. Workflow Artifacts

Successful discovery runs are converted into reusable JSON artifacts.

The current artifact schema version is:

```text
1.1
```

An artifact contains:

* artifact name and description
* application URL
* typed runtime inputs
* ordered workflow steps
* primary and fallback locators
* declared outputs
* business outcomes
* success checkpoint

The schema is defined using Pydantic and generated artifacts are validated before being saved.

### Supported Input and Output Types

```text
string
integer
boolean
```

### Supported Replay Actions

```text
fill
click
read
```

---

## 6. Runtime Parameterization

Discovery may use a real value such as:

```text
12345
```

The artifact builder compares recorded values with the discovery inputs.

Matching values are converted into runtime parameters:

```text
{{member_id}}
```

During replay, the runtime value is substituted back into the step.

For example:

```text
{{member_id}}
        ↓
runtime input
        ↓
12345
```

If an artifact requires a runtime input but the value is missing, replay raises a clear validation error rather than starting the browser with incomplete input.

For example:

```text
Missing required input: member_id
```

Template resolution also validates that a referenced runtime parameter exists before attempting to use it.

This allows one discovered workflow to be safely reused with different inputs.

---

## 7. Locator Strategy and Fallbacks

The artifact does not rely on only one browser selector.

For interactive controls, discovery can generate locator strategies using:

```text
id
name
label
role
```

Readable table values can use a deterministic CSS locator based on the row label.

For example:

```text
Savings Balance
```

can be converted into a selector targeting the second cell in the corresponding table row.

Each target contains:

```text
primary locator
fallback locators
```

During replay, the resolver tries the primary locator first.

If it does not uniquely identify a visible element, the resolver tries each fallback until a valid target is found.

If none of the stored strategies can resolve the element, replay returns a technical failure.

---

## 8. Structured Outputs

A `read` action can declare a reusable output name.

For example:

```json
{
    "action": "read",
    "save_as": "savings_balance"
}
```

During replay, the value is extracted from the page and stored in the result.

A successful replay can therefore return a structured response similar to:

```json
{
    "status": "success",
    "outputs": {
        "savings_balance": "$4,320.50"
    }
}
```

---

## 9. Business Outcomes

Expected business conditions are separated from technical automation failures.

For example, searching for an unknown member may display:

```text
Member not found
```

This is not treated as a browser automation failure.

Instead, replay can return:

```json
{
    "status": "business_outcome",
    "code": "member_not_found",
    "message": "The requested member was not found"
}
```

Tenant B similarly supports:

```text
customer_not_found
```

This makes the result clearer for callers because an expected business result is different from a broken locator or browser failure.

---

## 10. Checkpoints

Artifacts contain a final success checkpoint.

For Tenant A:

```text
Savings Balance
```

For Tenant B:

```text
Savings Amount
```

After all replay steps complete, the system verifies that the checkpoint text is present on the page.

If the expected checkpoint is missing, replay returns a structured `checkpoint_failed` technical failure.

---

## 11. Safety

The system applies safety checks before browser automation is allowed to proceed.

Safety is handled at two levels:

1. **URL safety** — controls which application origins and routes the automation may access.
2. **Action safety** — controls which browser actions may be executed automatically.

### URL and Route Allowlist

Before the configured target page is opened, both discovery and replay validate the target URL against an allowlist.

The prototype currently allows the local demo application through these origins:

```text
http://127.0.0.1:5000
http://localhost:5000
```

Approved route prefixes include:

```text
/
/member
/tenant-b
```

These cover the demo application's expected routes, including:

```text
/
/member/search
/tenant-b
/tenant-b/customer/search
```

A configured target outside the approved origin or route set is blocked before the initial Playwright navigation occurs.

For example:

```text
https://example.com
```

is blocked because its origin is not allowlisted.

Similarly:

```text
http://127.0.0.1:5000/admin
```

is blocked because `/admin` is not an approved route.

URL-safety decisions are written to the evidence log so that allowed or blocked navigation decisions can be inspected later.

### Action Allowlist

After navigation is approved, individual workflow actions are checked against the action safety policy before execution.

The currently allowed automated browser actions are:

```text
fill
click
read
```

Unknown or unsupported action types are blocked.

For example:

```text
download
```

is rejected because it is not part of the action allowlist.

### Blocked Operations

The prototype also checks target names for operations that should not be executed automatically.

Examples of blocked keywords include:

```text
delete
remove
close account
```

These actions return a blocked result instead of being executed.

### Human-Required Operations

Some operations require human involvement instead of automatic execution.

Examples include targets containing:

```text
transfer
payment
submit
confirm
```

These produce a:

```text
human_required
```

safety decision during replay.

The browser remains open so the user can perform the sensitive action manually before replay continues.

### Safety Tests

Automated tests verify both URL-level and action-level safety behavior.

The safety tests cover:

```text
normal action allowed
read action allowed
blocked destructive action
unsupported action blocked
payment requiring human interaction
approved Tenant A URL
approved Tenant B URL
external origin blocked
unapproved route blocked
```

This keeps the safety policy explicit and testable rather than relying only on runtime conventions.

---

## 12. Human Takeover

Replay supports human takeover for actions that should not be automatically completed.

When human takeover is required:

1. Automation pauses.
2. The current Playwright browser remains open.
3. The user manually performs the required action.
4. Cookies, page state, login state, and the existing browser session remain available.
5. The user returns to the terminal and presses Enter.
6. Automation resumes from the same browser session.

The sensitive step is not automatically executed after the human finishes it.

Replay records that the step was completed by the human and continues with the remaining workflow.

This allows automation to preserve the existing browser session while keeping sensitive operations under direct human control.

---

## 13. Evidence and Observability

Both discovery and replay generate JSON evidence files.

Each run records timestamped events and a final result.

Depending on the execution path, events can include:

```text
discovery_started
replay_started
url_safety_check
navigation_started
navigation_completed
navigation_blocked
observation_created
llm_decision
safety_check
action_executed
action_recorded
artifact_generated
step_started
step_completed
output_extracted
business_outcome
checkpoint_checked
action_blocked
step_failed
replay_completed
```

Evidence files are stored under:

```text
evidence/
```

For example, evidence can show:

* which artifact was executed
* which runtime inputs were supplied
* whether the target URL passed the safety policy
* which actions were attempted
* which locator was resolved
* which outputs were extracted
* whether a business outcome occurred
* whether a safety decision blocked execution
* whether the final checkpoint passed
* the final workflow result

This makes it possible to inspect what happened during a run instead of relying only on terminal output.

---

## 14. Multi-Tenant and Heterogeneous UI Support

The prototype demonstrates the same logical workflow across two different tenants.

### Tenant A

URL:

```text
http://127.0.0.1:5000
```

Input:

```text
member_id
```

UI terminology:

```text
Member Number
Search Member
Savings Balance
```

Example:

```text
12345 → $4,320.50
```

### Tenant B

URL:

```text
http://127.0.0.1:5000/tenant-b
```

Input:

```text
customer_id
```

UI terminology:

```text
Customer ID
Find Customer
Savings Amount
```

Example:

```text
C1001 → $8,120.75
```

Although the applications use different fields, labels, URLs, and result terminology, both use the same generic discovery and replay engines.

Tenant-specific configuration determines:

* target URL
* input name
* goal template
* artifact path
* checkpoint
* business outcomes

The core automation logic does not need a separate discovery or replay implementation for each tenant.

This is a prototype demonstration of heterogeneous tenant support. A production system would additionally require authentication, authorization, tenant data isolation, credential management, and persistent configuration storage.

---

## 15. Demo Application

The included Flask application provides the two example tenant interfaces used to demonstrate discovery and replay.

Tenant A sample data includes:

```text
12345
67890
55555
```

Tenant B sample data includes:

```text
C1001
C1002
```

The application intentionally uses different terminology between tenants so that discovery must create artifacts appropriate for each interface.

---

## 16. Project Structure

```text
computer-use-automation/
│
├── artifacts/
│   ├── get_savings_balance_generated.json
│   ├── get_savings_balance_broken.json
│   └── tenant_b_get_savings_balance.json
│
├── demo-app/
│   ├── app.py
│   └── templates/
│       ├── index.html
│       ├── member.html
│       ├── tenant_b.html
│       └── tenant_b_customer.html
│
├── evidence/
│   └── *.json
│
├── src/
│   ├── artifact/
│   │   ├── builder.py
│   │   ├── loader.py
│   │   ├── resolver.py
│   │   └── schema.py
│   │
│   ├── discovery/
│   │   ├── executor.py
│   │   ├── observer.py
│   │   ├── planner.py
│   │   └── recorder.py
│   │
│   ├── surface/
│   │   ├── base.py
│   │   ├── playwright_surface.py
│   │   └── __init__.py
│   │
│   ├── artifact_registry.py
│   ├── discover.py
│   ├── human_takeover.py
│   ├── logger.py
│   ├── replay.py
│   ├── run_discovery.py
│   ├── run_workflow.py
│   ├── safety.py
│   ├── tenant_config.py
│   └── __init__.py
│
├── tests/
│   ├── test_artifacts.py
│   ├── test_replay.py
│   └── test_safety.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 17. Setup

### Prerequisites

The project requires:

* Python 3
* pip
* Chromium installed through Playwright
* Groq API key for discovery

### Install Dependencies

From the project root:

```bash
pip install -r requirements.txt
```

The project uses:

* Flask
* Playwright
* Pydantic
* Groq
* python-dotenv
* pytest

### Install the Playwright Browser

```bash
playwright install chromium
```

### Configure Groq

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_groq_api_key
```

The `.env` file should not be committed to source control.

The project `.gitignore` should therefore include:

```text
.env
__pycache__/
.pytest_cache/
*.pyc
```

---

## 18. Start the Demo Application

From the project root, run:

```bash
python demo-app/app.py
```

The Flask application runs on:

```text
http://127.0.0.1:5000
```

Keep this terminal running while performing discovery or replay.

Open another terminal from the project root for the following commands.

---

## 19. Run Discovery

Discovery uses the LLM to determine the workflow and generate an artifact.

### Tenant A

```bash
python src/run_discovery.py tenant_a get_savings_balance 12345
```

The generated artifact is saved as:

```text
artifacts/get_savings_balance_generated.json
```

### Tenant B

```bash
python src/run_discovery.py tenant_b get_savings_balance C1001
```

The generated artifact is saved as:

```text
artifacts/tenant_b_get_savings_balance.json
```

Before opening the configured target, discovery checks whether its origin and route are allowed by the URL safety policy.

The Playwright browser is intentionally visible during discovery.

At the end of the run, press Enter in the terminal when prompted to close the browser.

---

## 20. Run Deterministic Replay

Replay uses the previously generated artifact.

The LLM planner is not used to decide the replay steps.

### Tenant A

```bash
python src/run_workflow.py tenant_a get_savings_balance 12345
```

Expected example output:

```text
Savings Balance: $4,320.50
```

### Tenant B

```bash
python src/run_workflow.py tenant_b get_savings_balance C1001
```

Expected example output:

```text
Savings Amount: $8,120.75
```

Replay:

1. loads the configured artifact
2. validates required inputs
3. checks the configured target against the URL safety policy
4. opens the approved target
5. executes the stored artifact steps
6. applies action-level safety checks
7. resolves stored locator strategies
8. extracts declared outputs
9. checks business outcomes
10. verifies the final checkpoint
11. writes structured evidence for the run

The LLM is not used to decide which workflow steps to execute during replay.

---

## 21. Try a Business Outcome

For Tenant A, use a member ID that does not exist:

```bash
python src/run_workflow.py tenant_a get_savings_balance 99999
```

Instead of treating the missing member as a browser failure, the workflow returns the configured business outcome:

```text
member_not_found
```

This demonstrates the distinction between an expected application-level result and a technical automation failure.

---

## 22. Run Tests

Run the complete test suite from the project root:

```bash
python -m pytest tests -v
```

The automated tests cover three main areas:

* artifact construction and validation behavior
* deterministic replay and runtime parameter resolution
* safety policy behavior

### Replay Tests

Replay tests verify:

* runtime template values resolve correctly
* different runtime inputs can reuse the same artifact parameter
* normal string values remain unchanged
* non-string values remain unchanged
* missing required runtime parameters raise an error

### Safety Tests

Safety tests verify:

* normal actions are allowed
* read actions are allowed
* destructive operations are blocked
* unsupported actions are blocked
* payment-related actions require human involvement
* Tenant A's configured URL is allowed
* Tenant B's configured URL is allowed
* external origins are blocked
* unapproved routes are blocked

At the time of final project verification, pytest reports:

```text
22 passed
```

All **22 automated tests pass**.

---

## 23. Discovery vs Replay

| Discovery                      | Replay                                        |
| ------------------------------ | --------------------------------------------- |
| Uses the LLM planner           | Does not use the LLM to choose workflow steps |
| Observes the current UI        | Loads a saved artifact                        |
| Decides actions dynamically    | Executes recorded steps                       |
| Records successful actions     | Resolves stored locators                      |
| Generates an artifact          | Consumes an artifact                          |
| Useful for learning a workflow | Useful for repeated execution                 |

The key design idea is:

> Use AI to discover the workflow, then use deterministic automation to repeat it.

The LLM is therefore used where flexibility is useful, while repeated execution is driven by the stored workflow definition.

---

## 24. Failure Handling

The system distinguishes several types of results.

### Success

```text
status = success
```

The workflow completed and the final checkpoint passed.

### Business Outcome

```text
status = business_outcome
```

The browser worked correctly, but the application returned an expected business condition such as:

```text
member_not_found
```

### Blocked

```text
status = blocked
```

The safety policy prevented an unapproved configured navigation or browser action from executing.

Examples include:

```text
external origin
unapproved route
unsupported action
destructive operation
```

### Human Required

Some operations should not be automatically completed.

For example:

```text
payment
transfer
confirm
submit
```

These operations can trigger human takeover so that the user performs the sensitive step manually.

### Technical Failure

```text
status = failure
```

Examples include:

* target locator cannot be resolved
* step execution fails
* browser/navigation error
* expected checkpoint is missing

A deliberately broken artifact is included in the project to support failure-handling demonstrations.

---

## 25. Current Limitations

This project is a prototype and intentionally keeps several areas simple.

Current limitations include:

* Discovery currently understands a limited set of UI elements.
* The observer primarily handles inputs, buttons, page text, and two-column table data.
* Artifact actions are limited to `fill`, `click`, and `read`.
* Business outcome conditions currently use text presence.
* Checkpoints currently use text presence.
* Locator generation currently includes `id`, `name`, `label`, and `role` strategies rather than relying exclusively on accessibility-tree-based identification.
* URL safety currently validates the configured target before initial navigation; broader enforcement across redirects and subsequent navigations would be a future extension.
* Automated retry handling for transient browser or loading failures is not currently implemented.
* The demo application runs locally.
* Tenant configuration is stored in Python rather than a persistent configuration service.
* Human takeover requires terminal interaction.
* Production authentication, authorization, tenant isolation, and credential management are outside the current prototype.

These boundaries keep the implementation focused on the core discovery-to-deterministic-replay architecture.

---

## 26. Possible Future Improvements

The prototype could be extended with:

* additional UI control types
* more action types
* stronger accessibility-based and semantic element identification
* more checkpoint and business outcome condition types
* screenshots and richer evidence
* screen recording for workflow demonstrations
* bounded retry policies for recoverable browser failures
* configurable timeouts
* URL safety enforcement across redirects and subsequent navigation
* persistent tenant/workflow registry
* artifact version migration
* browser session persistence
* authentication and secret management
* tenant-level authorization and isolation
* approval interfaces for human takeover
* remote applications instead of only the local demo
* broader use of the surface abstraction for additional automation environments

---

## 27. Summary

This project demonstrates a hybrid approach to browser automation.

**Discovery provides flexibility.**

An LLM observes an unfamiliar interface and determines how to accomplish a goal.

**Artifacts provide reusability.**

Successful discovery actions are converted into typed, parameterized, versioned workflow definitions.

**Replay provides determinism.**

Repeated execution follows the stored artifact instead of asking the LLM to rediscover the workflow.

**Safety provides execution boundaries.**

Configured target URLs are checked against origin and route allowlists, while individual browser actions are evaluated by a separate action safety policy. Sensitive operations can be blocked or handed over to a human.

**Evidence provides observability.**

Discovery and replay produce structured logs that make execution decisions and results inspectable.

**Multi-tenant configuration provides reuse across different interfaces.**

Tenant A and Tenant B use different URLs, input names, labels, and result terminology while sharing the same core discovery and replay engines.

Around this core flow, the prototype adds locator fallbacks, runtime input validation, structured outputs, business outcomes, checkpoints, URL and action safety controls, human takeover, evidence logging, **22 passing automated tests**, and multi-tenant UI support.
