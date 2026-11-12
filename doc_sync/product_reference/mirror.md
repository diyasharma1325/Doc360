# Whatfix Mirror Functional Reference

> Conceptual reference for Whatfix Mirror: product capabilities, terminology, feature scope, and
> relationships. Use to ground article drafts in accurate Mirror concepts and naming. Distilled
> from the **published** Mirror documentation (verified against the Document360 `mirror` workspace
> on 2026-09-25). Concepts only — for exact procedure steps, follow the `Source:` link. Each
> `Source:` URL is the canonical published article and may be used to **cross-link** from generated
> articles when relevant. FAQs and troubleshooting are folded into the relevant feature section (no
> separate dumps). Archived/deprecated/unpublished docs and Release Notes are excluded.

## Table of Contents

- **[Overview](#overview)** — Get Started, What is Mirror, Use Cases, DAP vs Mirror, Glossary
- **[Cross-Cutting Rules & Feature Relationships](#cross-cutting-rules--feature-relationships)** — staging, roles, Cloud/Beta gating, dependencies, when-to-use
- **[Administration: Security & Compatibility](#administration-security--compatibility)** — Browser Compatibility, Security, PII Handling, SLA, SSO, End-User Authentication, Email-Based Authentication, Approved Domains
- **[The Mirror Dashboard](#the-mirror-dashboard)** — Access & Manage, Lifecycle Stages, Publish, Share, Deployment Options
- **[Create Whatfix Mirror](#create-whatfix-mirror)** — Workflows & Simulations, Playground Mode, Capture & Manage Screens, Multi-Language
- **[Edit and Manage Mirror Screens](#edit-and-manage-mirror-screens)** — Edit Text, Blur, Replace, Smart Edits, Learner Experience (Nudges)
- **[Assessments](#assessments)** — Assessment Mode, Create, Pass Criteria, Hints, Best Practices
- **[Mirror with Roleplay](#mirror-with-roleplay)** — Conversation Types, Create an AI Roleplay (Builder or Manual), Persona, Attach/Detach, Analytics
- **[DAP Guidance on Mirror](#dap-guidance-on-mirror)** — Types, Create (per content type), Where it Appears, Visibility Rules, Flows, Pop-ups
- **[Organize Content: Task List & Self Help](#organize-content-task-list--self-help)**
- **[LMS Integration (SCORM/xAPI)](#lms-integration-scormxapi)**
- **[Mirror Analytics](#mirror-analytics)** — Workflow, Assessment, Roleplay, Trend Insights, Funnels

---

## Mirror Content Map (published IA snapshot)

> A snapshot of the Document360 category structure and published article inventory for the `mirror`
> workspace (128 published articles when it was taken). Use it to see where a feature is documented
> and which categories are likely to hold articles a change affects. It is not refreshed
> automatically, so the live workspace may have moved on since; the knowledge index (kb_index.py) is
> the up-to-date source for what is published now.

- **Whatfix Mirror Overview** (4) - Get Started with Whatfix Mirror · What is Whatfix Mirror? ·
  Whatfix Mirror Use Cases · Whatfix Mirror Glossary
- **Whatfix Administration** (8)
  - **→ Security and Compatibility** (8) - Browser Compatibility · Whatfix Security Overview ·
    Data Privacy and PII Handling in Mirror · Whatfix Service Level Agreement (SLA) · Set up
    Single Sign On · Set up End-User Authentication · Set Up Email-Based Authentication · Manage
    Approved Domains
- **Overview of the Whatfix Mirror Dashboard** (4) - Access and Manage the Mirror Dashboard ·
  Publish Whatfix Mirror · Share Whatfix Mirror · Mirror On-Premise Deployment
- **Create Whatfix Mirror** (18) - Understand Workflows and Simulations · Understand Playground
  Mode · Disable Playground Mode · Re-enable Playground Mode · Create a Mirror Workflow · Create a
  Simulation and add Mirror Workflows · Add a Mirror Screen to a Mirror Workflow · Recapture a
  Mirror Screen · Duplicate a Mirror Workflow or Simulation · Delete a Mirror Screen · Delete a
  Mirror Workflow · Rename a Mirror Workflow or Simulation · Pause and Resume a Mirror Capture ·
  Preview a Mirror Screen · Preview a Mirror Simulation · Manually Link a Mirror Screen ·
  Multi-Language Support in Mirror · Create Language Variants in Mirror
- **Edit and Manage Mirror Screens** (7) - Edit Text on a Mirror Screen · Blur an Image on a
  Mirror Screen · Replace an Image on a Mirror Screen · Smart Edits in Mirror · Apply Smart Edit
  Suggestions in Mirror · Customize the Learner Experience in Mirror · Customize Mirror Nudges
- **Assessments in Whatfix Mirror** (6) - What is Assessment Mode? · Create an Assessment ·
  Configure Hints for Assessments · Preview an Assessment · Share an Assessment · Best Practices
  for Assessments
- **Mirror with Roleplay** (13) - Introduction to Mirror Roleplay · Understand the Types of
  Roleplay Conversations · Create an AI Roleplay · Create an AI Roleplay using the AI Roleplay
  Builder · Create an AI Roleplay Manually · Configure a Persona for an AI Roleplay · Attach a
  Roleplay in Mirror · Preview a Roleplay in Mirror · Edit a Roleplay in Mirror · Detach a
  Roleplay in Mirror · Share a Roleplay in Mirror · Roleplay Analytics · Best Practices for Mirror
  with Roleplay
- **DAP Guidance on Mirror** (20) - Types of DAP Guidance on Mirror · Create DAP Guidance on
  Mirror · Configure Where DAP Guidance Appears · Push Whatfix Content and Widgets to Production ·
  Visibility and Display Rule Conditions · Create a Pop-up on Mirror · Create a Beacon on Mirror ·
  Create a Smart Tip on Mirror · Create a Launcher on Mirror · Create a Blocker on Mirror · Create
  a Cue on Mirror · Create a Survey on Mirror
  - **→ Pop-ups** (2) - What are Whatfix Pop-ups? · Create a Pop-up
  - **→ Flows** (6) - What are Flows? · Create a Flow · Preview a Flow on Mirror · Insert a video
    in a Flow step · Auto Flow Creation · Auto Create a Flow
- **Organize Whatfix Content** (3) - Create a Self Help on Mirror · Task List in Mirror · Create a
  Task List on Mirror
- **LMS Integration** (3) - Export a Mirror Workflow as a SCORM Package · Export an Assessment as
  a SCORM Package · Export a Mirror Roleplay as a SCORM Package
- **Mirror Analytics** (15) - Workflow Analytics · Assessment Analytics
  - **→ Product Analytics for Whatfix Mirror** (13)
    - **→ Trend Insights** (7) - Trend Insights in Mirror · Mirror Events in Trend Insights ·
      Create a Trend Insight in Mirror · Filter events using Event Filters and Breakdown in Trend
      insights · Understand Trend Insights in Mirror · Visualize an Assessment using Trend
      Insights · Visualize a Roleplay using Trend Insights
    - **→ Funnels** (6) - What are Funnel Insights? · Create a Funnel Insight for Mirror ·
      Understand Funnel Insights · Edit Funnel Insights for Mirror · Delete a Funnel step for
      Mirror · Filter Insights data using User filters and User breakdown in Mirrors
- **FAQs** (13) - Can Mirror automatically update Workflows or Simulations when there are changes
  in the underlying application’s UI or workflow? · Can Mirror be integrated with Learning
  Management Systems (LMS)? · Can I link multiple Mirror screens to an existing Mirror screen? ·
  Does Whatfix Mirror support multi-language functionality? · How can I access the Whatfix Mirror
  dashboard? · How does Mirror protect sensitive data in captured screens? · Is authentication
  required to view Mirror Flows through SCORM in an LMS? · What SCORM formats do Mirror Flows
  support in an LMS? · Is the Draft or Ready stage URL different from the Production URL in
  Mirror? · What are the components of a Mirror URL? · What deployment options are available for
  Mirror? · Where are the Mirror Screens saved? · Where can I find the Mirror Workflow ID?
- **Troubleshooting** (5) - Check if Smart Context is configured for your application · Error: The
  screen you're trying to access isn't available in the current stage · Stage mismatch error ·
  Unable to capture screens using Mirror · Unable to find the Mirror on the dashboard
- **Whatfix Mirror Release Notes** (9) - Q3 R1 2026 Mirror Release · Q2 R2 2026 Mirror Release ·
  Q1 R2 2026 Mirror Release · Q1 R1 2026 Mirror Release · Q4 2025 Mirror Release · Q3 R2 2025
  Mirror Release · Q3 R1 2025 Mirror Release · Q2 R2 2025 Mirror Release · Q1 R1 2025 Mirror
  Release

---

## Overview

### Get Started with Whatfix Mirror

**Source:** https://support.whatfix.com/mirror/docs/en/get-started-with-whatfix-mirror

Whatfix Mirror is application-simulation software that provides an immersive, interactive replica
of any web application — a hyper-realistic practice environment without the risk of a live system.
You can combine interactive screens with guidance overlays for additional learner support. Once
onboarded, a Whatfix representative helps define goals and measures ROI metrics (call volume, flow
usage, engagement, savings) before and after implementation.

### What is Whatfix Mirror?

**Source:** https://support.whatfix.com/mirror/docs/en/what-is-whatfix-mirror

Whatfix Mirror captures a sequence of screens and actions from a web application and automatically
connects them into a safe, controlled, risk-free environment where end users practice workflows
without real-world consequences. The captured screens also form the base for the Whatfix DAP
guidance layer (help guides, training content) without affecting the live application. Key
benefits: reduced training cost/IT overhead (no separate training environments or extra licenses),
risk-free practice, and simplified user management (training via a shared link or LMS, no training
accounts to provision).

**DAP vs Mirror (canonical distinction):** DAP provides in-context guidance *on the live
application* (Smart Tips, Flows overlaid on real workflows). Mirror creates a complete but
*isolated simulation* that users access from a shared web link or LMS — never the live app. Do not
conflate the two.

### Whatfix Mirror Use Cases

**Source:** https://support.whatfix.com/mirror/docs/en/whatfix-mirror-use-cases

Mirror replaces separate training/sandbox environments; multiple users can practice in the same
simulation without impacting the live app. Primary use cases: **Global Onboarding** (train
thousands across regions without per-user sandboxes), **Change Management & Guided Training**
(practice updated workflows before go-live, with Flows/Pop-ups/Smart Tips layered on),
**Analyze/Validate Skill Proficiency** (Assessments measure readiness before live access), and
**AI-Enabled Scenario Training** (Roleplay for conversational practice).

### Whatfix Mirror Glossary (key terms)

**Source:** https://support.whatfix.com/mirror/docs/en/whatfix-mirror-glossary

- **Mirroring** — cloning an application web page by capturing its entire UI.
- **Mirror Screen** — a replica of a single UI state/screen; the interactive unit of a Mirror.
- **Mirror Link** — connection between Mirror Screens, auto-created during capture (and manually
  linkable) so users navigate as in the live app.
- **Mirror Workflow** — a sequence of simulated screens guiding a user through one task (e.g. "How
  to create a Lead"). A self-contained user journey.
- **Mirror Simulation** — a container grouping related Workflows into one connected experience.
- **Playground Mode** — auto-links Workflows within a Simulation for free, non-linear navigation
  (on by default).
- **Assessment** — a guidance-free Simulation that evaluates how well users complete tasks.
- **Roleplay / AI Roleplay** — an AI-driven conversational simulation where an **Avatar** (the
  AI Persona) plays a role (customer, manager, etc.). Note: the published Glossary still defines
  the older Roleplay terms (**Series**, **Module**, **Copilot**), which the current AI Roleplay
  articles no longer use; ground Roleplay articles on the AI Roleplay articles below.
- **DAP Guidance / Guidance content** — Whatfix content (Flows, Pop-ups, Beacons, Smart Tips, Task
  List, Self Help) layered on a Mirror.
- **Smart Context** — Whatfix capability that auto-tags pages so Mirror can identify/link
  Workflows; must be configured before capture (auto for apps like Salesforce/SuccessFactors).
- **CLM (Content Lifecycle Management)** — the Draft/Ready/Production staging model (enabled by
  default for all Mirror accounts).
- Roles: only **Account Manager** and **Content Manager** can access the Mirror Dashboard.

---

## Cross-Cutting Rules & Feature Relationships

> The constraints, dependencies, and decisions that span Mirror features. Treat these as
> always-applicable when drafting or planning — they're the "gotchas" that make guidance accurate,
> and they shape which articles belong where.

### Lifecycle staging (Draft → Ready → Production)

- **Whatfix Studio shows only Draft content.** Once a Workflow moves to Ready or Production it
  disappears from Studio and is managed only from the Mirror Dashboard.
- **Authoring/editing actions are Draft-stage (often Draft/Ready) only:** capture/edit/redact
  screens, manual linking, duplicate, disable/re-enable Playground, create an Assessment, create,
  edit, attach or detach an AI Roleplay (Draft only; use **Edit in Draft** for a Production
  Roleplay), create Language Variants.
- **Sharing** is allowed from **Ready** (review with partners) or **Production** (learners) — never
  Draft. **Analytics are captured only in Production.**
- To change a live Workflow, use **Edit in Draft** — Whatfix creates a new Draft version while
  learners keep seeing the Production version.

### Roles

- Only **Account Manager** and **Content Manager** can access the Mirror Dashboard.
- **Account-Manager-only** actions include: configuring **SSO**, enabling **End-User
  Authentication**, and adding a **Language Variant**.

### Deployment & feature gating

- **Cloud vs On-Premise:** on-premise runs entirely on your servers but currently **lacks the
  Mirror Dashboard, Playground Mode, and Assessment Mode.**
- **Beta / add-on / enable-via-support features** (don't assume they're on): Playground Mode
  (Cloud only), **Smart Edits** (Cloud Beta), **Multi-Language / Language Variants** (Cloud Beta),
  **Email-Based Authentication** (Beta), **Auto Flow Creation** (GA, Cloud only), **Enhanced Screen Editing
  Experience** (Beta), **Blockers** and **Cues** (Beta, Cloud only), **Customisations** (Mirror
  Nudges and Assessment Hints; Beta, Cloud only), **Enhanced Guidance Deployment on Mirror** (GA),
  and **Mirror Roleplay** (add-on package via your CSM). **Roleplay is not supported on Safari.**

### Key dependencies & relationships

- **Smart Context must be configured (before capture)** for Playground Mode and Simulation
  auto-linking to work; auto for apps like Salesforce/SuccessFactors, manual for custom apps.
- **Mirror runs independently of DAP** — learners need no Whatfix install — **unless the Mirror
  contains DAP Guidance**, which then requires Whatfix and the guidance published to Production.
- **DAP Guidance on Mirror:** base-application guidance appears on Mirrors built from that same app
  by default; restrict with **Visible on = App / Mirror / both**. Guidance and Workflow have no
  stage dependency, but guidance must be in Production for learners to see it.
- **PII timing rule (critical):** editing/redacting **before** capture removes the original DOM
  (only a masked value is stored); **after** capture the original DOM is retained and edits only
  change the display. **Redact sensitive screens before capturing them.**
- **Language Variants re-capture** screens in the target language (they don't translate); the
  default variant is the original capture language.
- **SCORM/xAPI export is Production-only**, supports **SCORM 1.2** (plus **SCORM 2004** for a
  Workflow export) and **xAPI 1.0**, and requires the
  associated Guidance Flow's source URL to be the Mirror's **Production** URL; runs as **Slideshow**
  (static, no login) or **Live** (interactive, login if behind SSO).
- **Mirror does NOT support User Journeys** (it does support Trend Insights and Funnels).

### When to use which

- **Workflow vs Simulation** — a single task vs a group of connected tasks experienced together.
- **Playground ON vs OFF** — free, non-linear exploration vs an enforced fixed sequence
  (compliance, ordered training, assessments).
- **Blur vs Replace (image)** — partially obscure sensitive content vs remove/replace it entirely.
- **SSO vs Email-Based Authentication** — internal learners managed in your IdP vs external
  learners/partners (OTP, no IdP onboarding).
- **Conversion vs Productivity Funnel** — whether learners complete a task vs how fast they do.

---

## Administration: Security & Compatibility

### Browser Compatibility

**Source:** https://support.whatfix.com/mirror/docs/en/browser-compatibility

Mirror **creation** uses the Whatfix Studio browser extension, supported on Chromium browsers
(Chrome, New Edge). Content **deployment** supports a broader set (JavaScript embed or browser
extension on Firefox, Chrome, Safari, Edge Chromium). **Safari does not support Roleplay-enabled
Workflows.**

### Whatfix Security Overview

**Source:** https://support.whatfix.com/mirror/docs/en/whatfix-security-overview

When capturing a Mirror, Whatfix captures the webpage **DOM** needed to render the simulation and
support screen-level editing — **not** the application's business logic. Captured content (layout,
fonts, colors, images, icons) is stored, encrypted at rest, to enable accurate rendering,
versioning/revert, consistent edits, and localization. Access is governed by role-based controls.

### Data Privacy and PII Handling in Mirror

**Source:** https://support.whatfix.com/mirror/docs/en/data-privacy-and-pii-handling-in-mirror

Captured screens may contain personal/sensitive data; you are responsible for reviewing and
redacting it. The **Enhanced Screen Editing Experience** (Beta) lets you edit/redact PII before
and after capture. **When you edit content before capture, the original DOM is removed before it
leaves your browser** (only a masked original + replacement are stored). If you capture without
editing, the original DOM is stored; edits made *after* capture change the displayed simulation but
the original captured DOM remains. **FAQ — how does Mirror protect sensitive data?** Edit text,
blur images, or replace images on a screen before sharing.
(`how-does-mirror-ensure-that-sensitive-data-is-protected-during-simulations`)

### Whatfix Service Level Agreement (SLA)

**Source:** https://support.whatfix.com/mirror/docs/en/whatfix-service-level-agreement-sla

Contractual SLA: 99.9% Monthly Uptime commitment, Service Credit tiers, issue priorities (P1–P4)
with response/resolution targets, and support packages (Standard/Gold/Platinum). Reference only;
not product behavior.

### Set up Single Sign On (SSO)

**Source:** https://support.whatfix.com/mirror/docs/en/set-up-single-sign-on

SSO for the Whatfix Dashboard lets your team sign in with existing org credentials (e.g. Okta,
Azure AD). Configured via the Guidance Dashboard (Whatfix info → IdP info → Test and enable).
Enables Dashboard authentication, End-user authentication, and SSO-attribute segmentation. Note:
no SLO (single log out); the configuring admin must be assigned to the Whatfix app in the IdP.

### Set up End-User Authentication

**Source:** https://support.whatfix.com/mirror/docs/en/set-up-end-user-authentication

Prompts end users to authenticate via your org's SSO before they can access Whatfix content/Mirror.
Authentication can be scoped to **Guidance + Product Analytics** or **Mirror**. A secure cookie
(configurable expiry, 10 min–45 days) maintains the session. Only Account Managers can enable it;
requires Dashboard SSO first.

### Set Up Email-Based Authentication (Beta)

**Source:** https://support.whatfix.com/mirror/docs/en/set-up-email-based-authentication

An alternative end-user auth for **shared Mirror simulations** using email OTP, for external
learners/partners outside your IdP. Only learners whose email domain matches the approved whitelist
get an OTP (valid 10 minutes). An authenticated session lasts 7 days. SSO and Email-Based Auth can
both be enabled; when no auth is configured, the Mirror is publicly accessible.

### Manage Approved Domains

**Source:** https://support.whatfix.com/mirror/docs/en/manage-approved-domains

Define/manage the email domains authorized for Email-Based Authentication (whitelist up to 100
domains; add, disable, delete, edit). Learner email addresses used for authentication are not
stored or shown in analytics.

---

## The Mirror Dashboard

### Access and Manage the Mirror Dashboard

**Source:** https://support.whatfix.com/mirror/docs/en/access-and-manage-the-whatfix-mirror-dashboard

The centralized workspace to view, rename, preview, edit, delete, duplicate, and manage Workflows
and Simulations, add Assessments, manage Playground Mode, and move content across lifecycle stages.
**FAQ — how to access it?** From the Guidance Dashboard, use the **Product line switcher** and
select Whatfix Mirror. Only Content Manager and Account Manager roles can access it.
(`how-can-i-access-the-whatfix-mirror-dashboard`)

### Lifecycle Stages: Draft, Ready, Production

Workflows and Simulations progress through **Draft → Ready → Production** (CLM). Only **Draft**
content appears in Whatfix Studio; moving a Workflow to Ready/Production removes it from Studio.
Sharing/analytics: you can share in **Ready** (review with partners) or **Production** (final, with
learners); **analytics are captured only in Production**. **FAQ — are stage URLs different?** Yes —
Draft cannot be shared; Ready and Production each have distinct URLs.
(`is-the-draftready-url-different-from-the-production-url-in-mirror`) **FAQ — where are Mirror
Screens saved?** Studio saves captured screens within a Workflow; with CLM enabled (default), the
Workflow appears in Studio and the Dashboard's Draft stage.
(`where-are-the-mirror-screens-saved`)

### Publish Whatfix Mirror

**Source:** https://support.whatfix.com/mirror/docs/en/publish-whatfix-mirror

Publishing makes a Workflow/Simulation available to learners without granting live-app access.
Mirrors run independently of DAP (learners need not install Whatfix) — **unless** the Mirror
contains DAP Guidance, which requires Whatfix and the guidance to be published. Publishing a
Simulation respects Playground Mode (enabled → workflows experienced together; disabled →
individually). Without SSO, generated links are public.

### Share Whatfix Mirror

**Source:** https://support.whatfix.com/mirror/docs/en/share-whatfix-mirror

Share individual Workflows or Simulations via link (email/messaging), from the Ready or Production
stages only (not Draft, and not from Studio). For Simulations, the selected Workflow defines the
starting point; navigation depends on Playground Mode. Language variant is selectable at share
time. **FAQ — components of a Mirror URL:** ENT ID (account), Stage ID (present only with CLM),
Screen ID, Folder ID (present when a Roleplay is attached — used instead of Screen ID), Simulation
ID (present when an Assessment is added). (`what-are-the-components-of-a-mirror-url`)

### Deployment Options

**Source:** https://support.whatfix.com/mirror/docs/en/what-deployment-options-are-available-for-mirror

**Cloud Deployment** (Whatfix infrastructure; quick setup, seamless updates) or **On-Premise
Deployment** (runs entirely on your private servers — content/data/security stay in your
infrastructure; for highly regulated sectors). **On-premise note:** the Mirror Dashboard,
Playground, and Assessment Mode are currently unavailable on-premise
(`mirror-on-premise-deployment`). Delivery to learners: shareable URL, SCORM export, or xAPI
export.

---

## Create Whatfix Mirror

### Understand Workflows and Simulations

**Source:** https://support.whatfix.com/mirror/docs/en/understand-workflows-and-simulations

A **Workflow** is a self-contained sequence of Mirror Screens for one task; a **Simulation** groups
related Workflows. Adding Workflows to a Simulation auto-links them (via Playground Mode) to mimic
the real application. A Workflow can belong to multiple Simulations.

### Understand Playground Mode

**Source:** https://support.whatfix.com/mirror/docs/en/understand-playground-mode

Playground Mode lets users move freely between connected Workflows in a Simulation via Mirror Links
created during capture (only for elements you interacted with). On by default. Disable it to
enforce a fixed sequence (compliance/step-by-step training). **Prerequisite — Smart Context must be
configured before capture** so Mirror can identify and link Workflows; auto-generated for
out-of-the-box apps (Salesforce, SuccessFactors), configured manually for custom apps. Currently
Cloud-only. See also: Disable Playground Mode (`disable-playground-mode`), Re-enable Playground
Mode (`re-enable-playground-mode`). **Troubleshooting — verify Smart Context** via the browser
console command `_wfx_show_sc_config();` (`check-if-smart-context-is-configured-for-your-application`).

### Create a Mirror Workflow

**Source:** https://support.whatfix.com/mirror/docs/en/create-a-mirror-workflow

Capture a Workflow by interacting with your application in Whatfix Studio; Mirror auto-organizes
and links captured screens. The **Create guidance flow for the Workflow** checkbox (on by default)
auto-creates a Flow replicating the captured steps (see Auto Flow Creation). Supports non-linear
navigation (capture multiple elements on one screen for different paths). Redact sensitive content
before capture. Captured Workflows land in the Draft stage. **Troubleshooting — unable to capture
screens:** causes include Studio not detecting the element, app restrictions, two active Studio
extensions, or an outdated extension; fixes include clearing cache, ensuring one extension, and
reinstalling (`unable-to-capture-screens-using-mirror`). **Troubleshooting — Mirror not on the
dashboard:** Mirror Workflows appear on the **Mirror** Dashboard (Studio "Simulation" section), not
the Guidance Dashboard (`unable-to-find-the-mirror-on-the-dashboard`).

### Manage Workflows and Screens

Concept-level summary of the screen/workflow management articles:

- **Create a Simulation and add Workflows** — group Workflows; Playground Mode on by default
  (`create-a-simulation-and-add-workflows`).
- **Add a Mirror Screen to a Workflow** — capture new screens (before/after a selected screen) as
  the app evolves; auto-linked (`add-a-mirror-screen-to-a-mirror-workflow`).
- **Recapture a Mirror Screen** — refresh a screen after a UI change while keeping its place;
  recapture does **not** include the associated element, so re-link it
  (`recapture-a-mirror-screen`). **FAQ — does Mirror auto-update on app changes?** No; manually
  recapture or edit affected screens (the architecture eases per-element updates without recapturing
  the whole Workflow) (`can-mirror-automatically-update-simulations-...`).
- **Duplicate a Workflow or Simulation** — copy structure/content (Draft/Ready only; duplicating a
  Simulation with an Assessment omits the Assessment; duplicating a Workflow keeps its attached
  Roleplay) (`duplicate-a-mirror-workflow-or-simulation`).
- **Delete a Mirror Screen / Workflow** — irreversible; keep the link between previous/next screen
  when deleting a screen (`delete-a-mirror-screen`, `delete-a-mirror-workflow`).
- **Rename a Workflow or Simulation** (`rename-a-mirror-workflow-or-simulation`).
- **Pause and Resume a Mirror Capture** — pause to skip unwanted screens (e.g. a stray pop-up)
  during capture (`pause-and-resume-a-mirror-capture`).
- **Preview a Mirror Screen / Simulation** — verify interactive elements and Playground navigation
  before publishing (`preview-a-mirror-screen`, `preview-a-mirror-simulation`).
- **Manually Link a Mirror Screen** — link screens when one screen has multiple clickable elements
  leading to different destinations (Draft stage only) (`manually-link-a-mirror-screen`). **FAQ —
  can I link multiple screens to an existing screen?** Yes — this creates the interactive
  navigation of the simulation (`can-i-link-multiple-mirror-screens-to-an-existing-mirror-screen`).

### Multi-Language Support in Mirror (Beta)

**Source:** https://support.whatfix.com/mirror/docs/en/multilanguage-support-in-mirror

Create localized **Language Variants** of a Workflow. Whatfix **re-captures** screens in the target
language (rather than translating), keeping the same structure/sequence; variants are stored within
the same Workflow and share its lifecycle stage. Applies to Workflows, Workflows in a Simulation,
and Assessments. **The default language variant is the language of original capture.** To create a
variant: add the language on the Guidance Dashboard, then automate re-capture in Studio with the
app set to that language (`create-language-variants-in-mirror`). **FAQ — does Mirror support
multi-language?** A given Mirror captures the app's language at capture time; changing the app
language later does not update an existing Mirror — use Language Variants / re-capture
(`does-whatfix-mirror-support-multi-language-functionality`).

---

## Edit and Manage Mirror Screens

> Redaction/editing applies only in the **Draft** stage (Ready/Production don't appear in Studio).
> Edits are **permanent** (no restore of the original text/image after applying). Edit scope can be:
> instance, this screen, or all screens in the workflow.

### Edit Text on a Mirror Screen

**Source:** https://support.whatfix.com/mirror/docs/en/edit-text-on-a-mirror-screen

Replace/remove sensitive text (emails, phone numbers, account IDs) or update labels/placeholders,
before or after capture. A "Recommendations" icon surfaces AI Smart Edit suggestions.

### Blur / Replace an Image on a Mirror Screen

**Sources:** https://support.whatfix.com/mirror/docs/en/blur-an-image-on-a-mirror-screen ·
https://support.whatfix.com/mirror/docs/en/replace-an-image-on-a-mirror-screen

**Blur** hides sensitive image content at adjustable intensity (25/50/75/100%); **Replace**
swaps an image entirely (e.g. a confidential chart) — useful when blurring is insufficient. JPG/PNG
only; replacement images < 10 MB. Background images can't be blurred.

### Smart Edits in Mirror (Beta)

**Source:** https://support.whatfix.com/mirror/docs/en/smart-edits-in-mirror

AI-powered detection of potential **PII** on captured screens — flags elements with a **yellow
outline** and suggests text/image redactions you review and apply individually (in Studio or the
Dashboard). Detected categories include identity documents/numbers (SSN, ITIN, Aadhaar, PAN, NIN,
passport), contact/personal info (emails, phone, names, addresses), financial data (card/bank
numbers), dates and technical identifiers (IPs, MAC, session/transaction IDs), and visual content
(faces/IDs). Cloud-only Beta; image detection JPG/PNG only; suggestions are recommendations and
don't change the original captured DOM. Applying via the dashboard:
`apply-smart-edit-suggestions-in-mirror`.

### Customize the Learner Experience (Beta)

**Sources:** https://support.whatfix.com/mirror/docs/en/customize-the-learner-experience-in-mirror ·
https://support.whatfix.com/mirror/docs/en/customize-mirror-nudges

**Customisations** (Mirror Dashboard → Settings → Customisations; Beta, Cloud only) control how
learners are helped when they click the wrong element. Two kinds: **Mirror Nudges** (Workflows and
Simulations) highlight the target element after a set number of incorrect clicks, and
**Assessment Hints** (Assessments; see below) show a hint message instead. Mirror Nudges are **on
by default**; the number of attempts defaults to 1 and resets on each new Mirror Screen or page
refresh; color, highlight and animation are configurable. All Customisation settings are
**account-level**: they apply to every Mirror Screen, in SCORM and non-SCORM deployments, in
Playground Mode, and across Language Variants.

---

## Assessments

### What is Assessment Mode?

**Source:** https://support.whatfix.com/mirror/docs/en/assessment-mode

An Assessment is a **guidance-free** Simulation (all Smart Tips/Flows removed) that evaluates how
proficiently users complete tasks unassisted. A Task List shows the Workflows to complete and tracks
progress in real time; performance (attempts, pass/fail, completion rate) is tracked automatically
and shown in Mirror Analytics. Customize via **Pass Criteria** (complete all, or N Workflows),
**Start/End screen Pop-ups**, and **Playground Mode**.

### Create an Assessment

**Source:** https://support.whatfix.com/mirror/docs/en/create-an-assessment

Assessments apply to **Simulations only** (add Workflows to a Simulation first), created in Draft
or Ready. Set Pass Criteria to define proficiency. See also **Best Practices for Assessments**
(`best-practices-for-assessments`), Preview (`preview-an-assessment`), Share (`share-an-assessment`).

### Configure Hints for Assessments (Beta)

**Source:** https://support.whatfix.com/mirror/docs/en/configure-hints-for-assessments

By default an Assessment shows no Mirror Nudges and no DAP Guidance, so learners work unaided.
**Assessment Hints** (Settings → Customisations → Assessments; Beta, Cloud only) add a global hint
message after a set number of incorrect attempts (default 1), optionally with a Mirror Nudge on
the target element, **without** turning on DAP Guidance. Hints are **disabled by default**, and
disabling them also suppresses Mirror Nudges in Assessments. The setting is account-level and
applies to every Assessment, in every language.

---

## Mirror with Roleplay

> Roleplay is an **add-on** package; enable via your Customer Success Manager. It adds an AI-driven
> conversational layer on top of Mirror's workflow simulation. The current articles call the
> feature **AI Roleplay** and manage it from the **AI Roleplay** tab of the Whatfix Mirror
> Dashboard. **Not supported on Safari.**

### Introduction to Mirror Roleplay

**Source:** https://support.whatfix.com/mirror/docs/en/introduction-to-mirror-roleplay

An **Avatar** (the AI Persona) takes on a role (customer, manager, stakeholder) and responds
dynamically to the learner, so learners practice interpersonal and decision-making skills in a
risk-free environment (e.g. de-escalating a frustrated customer). Benefits: real-time adaptive
simulation, faster onboarding, no risk to live systems, and AI-driven feedback with session
recordings. Use cases: customer support, sales enablement, insurance claim handling.

### Understand the Types of Roleplay Conversations

**Source:** https://support.whatfix.com/mirror/docs/en/understand-the-types-of-roleplay-conversations

The **Conversation type** is selected on the Persona tab when you create a Roleplay and can be
changed later: **Cold Calling, Negotiation, Discovery, Renewal Management, Product Pitch, Mutual
Discovery, Competitive Differentiation, Inbound Call, Discovery with Evaluation,** and **Custom
Roleplay Scenario** (organization-specific needs, via your CSM). The published name is
"conversations"; "scenario" survives only in the Custom type's name.

### Create an AI Roleplay

**Sources:** https://support.whatfix.com/mirror/docs/en/create-an-ai-roleplay ·
https://support.whatfix.com/mirror/docs/en/create-an-ai-roleplay-using-the-ai-roleplay-builder ·
https://support.whatfix.com/mirror/docs/en/create-an-ai-roleplay-manually

An AI Roleplay has five components: **Avatar instructions** (the situation, the Persona's emotional
baseline and triggers, what it withholds, and when the conversation counts as resolved), the
**Avatar** (Persona), **Evaluation**, **End conditions** (Exit conditions in the UI), and the
**Learner brief**. Two ways to create one, both from **AI Roleplay → + AI Create Roleplay** in the
**Draft** stage only:

- **AI Roleplay Builder** (Whatfix's recommended path): describe the scenario (10 words to 2,000
  characters) or upload a call transcript or reference document (.doc, .docx or .txt, up to 5 MB;
  images are ignored; avoid PII). Whatfix generates the Persona, emotional state, learner role and
  objective, evaluation parameters, **Modality** (Voice or Chat) and **difficulty level** (Easy,
  Medium or Hard) for review, then **Generate detailed scenario**.
- **Create manually**: name the Roleplay, choose the Modality (**Audio roleplay**, the default, or
  **Chat roleplay**), and write the scenario yourself.

Both paths then share the same tabs. **Scenario**; **Persona** (choose or create a Persona, pick
the Conversation type, choose who speaks first, set opening and closing messages);
**Evaluation** (up to **10 parameters**, each of type **Rating** (recommended), **Text**, **Single
Choice** or **Multiple Choice**, with competencies, scoring guidance and good/poor reference
responses); **Exit conditions** (session up to **15 minutes**, a repetition limit up to **5**,
plus custom end rules); **Learner info** (the Learner brief, up to **500 characters**; the
Builder generates it, and editing it overrides the generated version). Changes are not saved
automatically, and the preview reflects only the last saved version. Finally, **Attach to
workflow**: every new AI Roleplay is created in Draft and must be attached to a Workflow before it
moves to Ready or Production.

### Configure a Persona for an AI Roleplay

**Source:** https://support.whatfix.com/mirror/docs/en/configure-a-persona-for-an-ai-roleplay

A Persona has a **Name, Job title, Gender, Language, Voice** (regional accent variant) and
**Behavioural description**, plus an optional image. Whatfix supports **406 voices across 26
languages** (updated periodically; the Voice dropdown is the current source). Personas can be
created in the Builder, created manually on the Persona tab, or changed with **Change persona**.
**Persona attributes are shared:** editing one applies to every Roleplay that uses it.

### Manage Roleplays in Mirror

Concept-level summary:

- **Attach**: attach an AI Roleplay to a Workflow, or a Workflow to an AI Roleplay (Draft only). A
  badge names the attached item, and the pair then **moves together across stages**
  (`attach-a-roleplay-in-mirror`).
- **Preview**: preview the AI Roleplay alone (**Preview AI Roleplay → Start Session**) or the
  combined experience (**Preview with Roleplay** on the Workflow). Ready-stage activity is not
  recorded in analytics (`preview-a-roleplay-in-mirror`).
- **Edit**: edit any tab or rename the Roleplay, in Draft only; use **Edit in Draft** for a
  Production Roleplay (`edit-a-roleplay-in-mirror`).
- **Detach**: detach to restrict learner access temporarily while you update it (Draft only). A
  detached Roleplay cannot be previewed or shared as a Mirror with Roleplay link, and the pair no
  longer moves across stages together (`detach-a-roleplay-in-mirror`).
- **Share**: from Ready (internal review, no analytics) or Production, choosing a Language Variant
  and either **Workflow with roleplay** or **Workflow without roleplay**. For an LMS, export a
  SCORM package instead (`share-a-roleplay-in-mirror`).

### Roleplay Analytics

**Source:** https://support.whatfix.com/mirror/docs/en/roleplay-analytics

Mirror Dashboard → Analytics → **AI Roleplay**, per Workflow. The **Activity** tab tracks two
events (**Workflow or Roleplay started**, **Workflow and Roleplay completed**) across All activity,
Unique users and a User level breakdown; **View details** opens per-attempt feedback (conversation
length, overall score 0 to 100, per-parameter scores, positive and constructive feedback).
Available only after learners use a **published and shared** Roleplay; attempts under **one
minute** generate nothing. Users are identified by cookie, or by User ID when SSO is configured.
See also **Best Practices for Mirror with Roleplay** (learner-brief design, Persona design, and
testing the happy path and deviation scenarios before rollout)
(`best-practices-for-mirror-with-roleplay`), and **Visualize a Roleplay using Trend Insights**
(`visualize-a-roleplay-using-trend-insights`).

---

## DAP Guidance on Mirror

### Types of DAP Guidance on Mirror

**Source:** https://support.whatfix.com/mirror/docs/en/types-of-dap-guidance-on-mirror

DAP Guidance you can layer on Mirror: **Flows** (step-by-step walkthroughs), **Pop-ups** (contextual
messages), **Beacons** (attention markers), **Smart Tips** (contextual tooltips), **Blockers**
(Beta — restrict interaction until a step is done), **Cues** (Beta — non-intrusive slide-in
nudges), **Task Lists** (trackable task sets), and **Self Help** (in-app help panel). By default,
DAP guidance configured for a base application appears on Mirror simulations built from that same
application. (For the shared concept definitions of each content type, see `dap-core`.)

Each content type also has a Mirror-specific create article with Mirror use cases: Pop-up
(`create-a-pop-up-on-mirror`), Beacon (`create-a-beacon-on-mirror`), Smart Tip
(`create-a-smart-tip-on-mirror`), **Launcher** (`create-a-launcher-on-mirror`; a button that
triggers a Flow, Pop-up, video or link), Blocker (`create-a-blocker-on-mirror`; Beta, Cloud only;
Visible Blockers tooltip on hover, Invisible ones on click), Cue (`create-a-cue-on-mirror`; Beta,
Cloud only), and **Survey** (`create-a-survey-on-mirror`; collects learner feedback after a
Workflow). Launchers and Surveys have create articles but are not in the Types article's list.

### Create DAP Guidance on Mirror

**Source:** https://support.whatfix.com/mirror/docs/en/create-dap-guidance-on-mirror

Create guidance in Whatfix Studio, configure visibility rules (base app, Mirror, or both), preview
on the Mirror URL, then publish both the guidance and the Mirror Workflow to Production. For Flows
intended for SCORM export, use the Mirror Workflow's **Production** URL as the Flow source URL
before publishing.

### Configure Where DAP Guidance Appears

**Source:** https://support.whatfix.com/mirror/docs/en/configure-where-dap-guidance-appears

By default, base-app guidance also appears on Mirrors built from that app. Use the **Visible on**
visibility-rule setting to restrict guidance to **App** only or **Mirror** only (e.g. compliance
reminders on the live app but not in training; detailed step guidance on Mirror but not live). DAP
Guidance and Mirror Workflows have no stage dependency, but to show guidance to learners on a
Production Workflow, publish the associated guidance to Production.

### Visibility and Display Rule Conditions

**Source:** https://support.whatfix.com/mirror/docs/en/visibility-and-display-rule-conditions-for-dap-guidance

**Visibility Rules** define where/to whom widgets (Task List, Self Help) appear (set on the
Guidance Dashboard while creating segments). **Display Rules** define when tooltips appear for
content like Flows/Smart Tips (set in Studio). Conditions include URL Properties, Other Element on
Page, Window Variable, Attribute conditions (User/Enterprise), Selected Element (CSS/jQuery or
text), User Action, and Tags (Page/Role). Whatfix recommends "Selected Element Is" (CSS) over text.

### Flows on Mirror

**Source:** https://support.whatfix.com/mirror/docs/en/what-are-flows-1

Flows are step-by-step overlays that walk learners through a task on the mirrored app. Mirror-
specific Flow articles cover Create (`create-flows`), Preview on Mirror via **See Live** vs
**Preview Mode** (`preview-a-flow-on-mirror`), and Insert a video in a Flow step
(`inserting-a-video-in-a-flow-step`). **Auto Flow
Creation** (GA, Cloud only) auto-generates a Flow from a captured Workflow with a description for
each step, created when the "Create guidance flow" checkbox (selected by default) is on during
capture, and **keeps it in sync**: adding, removing or recapturing screens updates the Flow, and its
Source URL follows the Workflow's stage URL. Branching is not supported (`auto-flow-creation`,
`auto-create-a-flow`). Whether a Pop-up or Flow targets the Mirror Screen URL or the base
application URL depends on whether **Enhanced Guidance Deployment on Mirror** is enabled.

### Pop-ups on Mirror

**Source:** https://support.whatfix.com/mirror/docs/en/what-are-whatfix-pop-ups

Overlay messages for onboarding, training-update announcements, and emphasizing key actions in a
simulation. A Pop-up does not anchor to an element, so it sets context for the whole Mirror Screen
(e.g. a welcome message on the first screen that launches a Flow), and can carry a Flow, video,
image or GIF. Built with the **Visual Editor** (drag-and-drop, up to 24 components in a 6×4 grid;
6 templates; carousel support) from Studio or the Dashboard, then scoped with Visibility Rules.
Articles: Create a Pop-up (`create-a-pop-up`), Create a Pop-up on Mirror
(`create-a-pop-up-on-mirror`).

---

## Organize Content: Task List & Self Help

### Task List in Mirror

**Sources:** https://support.whatfix.com/mirror/docs/en/task-list-in-mirror ·
https://support.whatfix.com/mirror/docs/en/create-a-task-list-on-mirror

Task Lists work inside the mirrored app, giving learners a trackable set of to-do tasks (accessible
from a configurable icon, typically bottom-left, and marked with a green checkmark as each is
completed) that can trigger other content like Flows. Use for new-employee onboarding and process
learning. Task Lists can be segmented via Visibility Rules, and must be pushed to Production like
other widgets (`pushing-whatfix-content-to-production`).

### Self Help on Mirror

**Source:** https://support.whatfix.com/mirror/docs/en/create-a-self-help-on-mirror

An in-app panel, available anywhere on the Mirror Screen, that collects Flows, videos and articles
you select so learners can search for and open guidance on demand while practicing a Workflow.

---

## LMS Integration (SCORM/xAPI)

**Sources:** Export a Mirror Workflow (`export-a-mirror-workflow-as-a-scorm-package`) · an
Assessment (`export-an-assessment-as-a-scorm-package`) · a Roleplay
(`export-a-mirror-roleplay-as-a-scorm-package`)

Export Mirror Workflows, Assessments, or Roleplays as a **SCORM** package (a .zip uploaded to a
SCORM-compliant LMS) so learners access the simulation from the LMS. Whatfix supports **SCORM 1.2**
and **xAPI 1.0** (only one export option enabled at a time; enable via support); a **Workflow**
export also offers **SCORM 2004** and an **Include Assessments as training** toggle. **The exported
package includes only Flows/content in the Production stage.** A Workflow export requires its
associated **Guidance Flow** linked to the Workflow's Production-stage URL (auto-created if the
Workflow used Auto Flow Creation). DAP Guidance (Pop-ups/Smart Tips/Beacons) appears in the package
only if both the Workflow and the widgets are in Production. **FAQ — SCORM formats & auth:** Flows
run in **Slideshow Mode** (static captured screens, no login needed) or **Live Mode** (interactive,
login required if the screen is behind SSO) (`what-scorm-formats-do-mirror-flows-support-in-an-lms`,
`is-authentication-required-to-view-mirror-flows-through-scorm-in-an-lms`). **FAQ — LMS
integration?** Yes, via SCORM or xAPI (`can-mirror-be-integrated-with-learning-management-systems-lms`).

---

## Mirror Analytics

> Analytics are captured only for content shared in the **Production** stage. Users are identified
> by browser cookie by default, or by configured User ID when SSO is enabled.

### Workflow & Assessment Analytics

**Sources:** `workflow-analytics` · `assessment-analytics`

The built-in Mirror Analytics Dashboard tracks how learners engage with and perform in Workflows and
Assessments (participation, completion, attempts, pass/fail). Assessment results appear after
learners complete a shared/published or SCORM-exported Assessment.

### Trend Insights in Mirror

**Source:** https://support.whatfix.com/mirror/docs/en/trend-insights-in-mirror

Trend Insights turn engagement queries into visual insights (e.g. users who started vs completed a
Workflow), auto-created after you build a Mirror. Built from Metrics (Total events, Unique users),
Events, Event Filters/Breakdowns, and User Filters/Breakdowns
(browser, OS, city, country). The Mirror events are **Workflow Started**, **Workflow Completed** and
**Mirror Screen Viewed** (Workflow); **Assessment Attempted** and **Assessment Passed**
(Assessment); and the Roleplay events (`mirror-events-in-trend-insights`). **FAQ — find the
Workflow ID:** every Workflow has a unique ID, which appears in the Mirror's
URL after `.../service/mirror/server/` (`where-do-i-find-the-mirror-folder-id`).

### Funnels (Conversion & Productivity)

**Source:** https://support.whatfix.com/mirror/docs/en/what-are-funnel-insights

A Funnel is a sequence of events tracking how learners progress through a Workflow — completion
rates, drop-off points, and time per step. **Conversion Funnels** measure whether learners complete
the task; **Productivity Funnels** measure how fast (add a completion-time filter). Funnel steps can
be Flows, Workflows, Custom events, or Page views. Auto-generated for each Workflow and auto-updated
on Workflow changes. The Funnel View shows drop-off slopes and a summary (Average/Median/95th-
percentile completion time, Slowest Step, Biggest Drop); the Table View maps steps to Mirror Screens
and unique users. Articles: Create (`create-a-funnel-insight-for-mirror`), Understand
(`understand-funnel-insights`), Edit (`edit-funnel-insights-for-mirror`), Delete a step
(`delete-a-funnel-step-for-mirror`), Filters/Breakdown
(`filter-insights-data-using-user-filters-in-mirror`).

> Note: Whatfix Mirror does **not** support User Journeys (per the Mirror Glossary).

---

## Troubleshooting (folded references)

These troubleshooting articles are folded into the sections above; consolidated for lookup:
- **Smart Context not configured** → see Playground Mode / Create a Mirror Workflow.
- **"Screen isn't available in the current stage" / Stage mismatch error** → a CLM stage mismatch
  between a Flow and the Mirror; keep the Flow and Mirror in the same stage and use the matching
  stage-specific Mirror URL (`error-the-screen-youre-trying-to-access-isnt-available-in-the-current-stage`,
  `stage-miss-match`). See DAP Guidance on Mirror / Share.
- **Unable to capture screens** → see Create a Mirror Workflow.
- **Unable to find the Mirror on the dashboard** → see The Mirror Dashboard.
