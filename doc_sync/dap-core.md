# Whatfix DAP Core Functional Reference (surface-agnostic)

> Conceptual reference for the Whatfix Digital Adoption Platform (DAP): what it is, its content
> types, how content is authored and targeted, and the canonical names for each. This is the
> SHARED model across every DAP surface (Web, Desktop, Mobile, OS); Web is the primary surface.
> Surface-specific capture/deployment/limits live in the surface delta references
> (`dap-web`, and future `dap-desktop` / `dap-mobile` / `dap-os`).
>
> Distilled from the **published** DAP documentation, **verified against the live Document360
> `studio` (DAP Web) workspace on 2026-09-25** (Release Notes and
> Contact Support excluded). Concepts only — for exact procedure steps, follow the `Source:` link,
> which is also a valid **cross-link** target. The Content Map below is the CURRENT published IA;
> fit new articles into it and don't duplicate an existing title. Core authoring is covered in
> depth; peripheral areas (deployment, integrations, analytics, translations) are covered as
> overviews (retrieval has their detail). FAQs and troubleshooting are folded/summarized, not
> enumerated. Archived/deprecated/unpublished docs are excluded.

## Table of Contents

- **[DAP Content Map (current published IA)](#dap-content-map-current-published-ia)**
- **[Overview](#overview)** — What is Whatfix, where used, content umbrella, Studio, Dashboard, CLM stages, Workflow, Roles
- **[Cross-Cutting Rules & Feature Relationships](#cross-cutting-rules--feature-relationships)** — CLM staging, roles, Beta gating, dependencies, when-to-use
- **[Content Types (the DAP primitives)](#content-types-the-dap-primitives)** — Flows, Smart Tips, Beacons, Pop-ups, Launchers, Cues, Surveys, Task List, Blocker, Static Content
- **[End-User Widgets: Self Help & Hub](#end-user-widgets-self-help--hub)** — Self Help, Hub, QuickRead
- **[Targeting & Delivery](#targeting--delivery)** — Segmentation, Tags, Visibility Rules (new & old), User Attributes, Custom Variables, User Identification
- **[Element Detection & Resilience](#element-detection--resilience)** — ScreenSense, Smart Context, Auto reselect, Auto-heal
- **[AI Capabilities](#ai-capabilities)** — Authoring / Guidance / Insights Agents
- **[Authoring Lifecycle (overviews)](#authoring-lifecycle-overviews)** — Translations, Multi-format Outputs, Archival & Versioning, Testing & Diagnostics
- **[Analytics (overview)](#analytics-overview)** — Guidance Analytics
- **[Integrations (overview)](#integrations-overview)** — Integration Hub, Content Aggregation
- **[FAQs & Troubleshooting (folded)](#faqs--troubleshooting-folded)**
- **[Glossary](#glossary)**

---

## DAP Content Map (current published IA)

> The live Document360 category structure and published article inventory for the `studio`
> workspace (1363 published articles), derived from the Tier-2 index at read time. Use as the IA
> baseline: fit new articles into this structure, don't duplicate an existing title, and place
> enhancements in the right category. Every published category is listed, including Release Notes
> and Contact Support.

- **Whatfix Web Overview** (11)
- **Whatfix Administration** (33) - 2 directly here
  - **→ User Management** (8)
  - **→ Security and Compatibility** (16) - 1 directly here - sub: GXP Compliance Ready (1) ·
    FAQs: Security and Compliance (14)
  - **→ FAQs: Account Administration** (7)
- **Accessibility** (8) - 5 directly here
  - **→ FAQs: Accessibility** (3)
- **Create Whatfix Content** (346) - 5 directly here
  - **→ In-app Content** (187) - 1 directly here - sub: Flows (54) · Smart Tips (26) · Beacons
    (18) · Pop-ups (37) · Survey (23) · Launcher (14) · Blocker (2) · Cues (12)
  - **→ Static Content** (6)
  - **→ Visibility and Display Rule Conditions** (11)
  - **→ New Visibility Rules** (44) - 1 directly here - sub: New Visibility Rules for Widgets (28)
    · New Visibility Rules for Content (10) · FAQs: New Visibility Rules (5)
  - **→ Publish Whatfix Content** (4)
  - **→ Multi Format Outputs** (24) - 5 directly here - sub: Whatfix PDF Export (3) · Whatfix ODF
    Export (2) · Whatfix Videos (10) · Whatfix Slideshows (3) · Whatfix Links (1)
  - **→ Translations** (38) - 11 directly here - sub: Translate Whatfix Content (12) · Translation
    Status (2) · Custom Translation Tool (2) · FAQs: Translations and Language Support (11)
  - **→ Content Archival** (3)
  - **→ Preview Whatfix Content** (8)
  - **→ Manage Whatfix Content and Widgets** (7)
  - **→ FAQs: Dashboard** (9)
- **Configure Whatfix Content** (51) - 8 directly here
  - **→ Improve Element Selection using Element Reliability indicators** (2)
  - **→ Understand Advanced Customization** (3)
  - **→ Configure Global Settings using Technical Configurations** (29)
  - **→ Configure User and Locale identification rules** (5)
  - **→ Configure Custom Variables to Personalize Whatfix Content** (1)
  - **→ Icon Library** (3)
- **Organize Whatfix Content** (119)
  - **→ Segmentation** (114) - 1 directly here - sub: Tags for Segmentation (6) · User Roles for
    Segmentation (1) · User Attributes for Segmentation (2) · Self Help (83) · Task List (21)
  - **→ ScreenSense** (5)
- **Deploy Whatfix Content** (74)
  - **→ Choose a Delivery method** (24) - sub: Use JavaScript to deliver your content (13) · Use
    Browser Extension to deliver your content (11)
  - **→ Plan Content Release** (2)
  - **→ Choose a Deployment method** (6) - 1 directly here - sub: Self Host Whatfix content (5)
  - **→ Deploy Whatfix extensions on your end user's devices** (18) - sub: Deploy Whatfix
    Extension using an Endpoint Management Tool (17) · Deploy Whatfix extensions on different
    browsers manually (1)
  - **→ FAQs: Deployment and Delivery** (24)
- **Test Whatfix Content** (36)
  - **→ Test cases** (6)
  - **→ Test Suites** (9)
  - **→ Login Flows** (1)
  - **→ Test Settings** (2)
  - **→ FAQs: Auto Testing** (18)
- **Content Aggregation** (26) - 9 directly here
  - **→ SharePoint Integration** (3)
  - **→ OneDrive Integration** (2)
  - **→ ServiceNow Integration** (1)
  - **→ Freshservice Integration** (1)
  - **→ Confluence Repository Integration** (1)
  - **→ Salesforce Integration** (2)
  - **→ Sharefile Integration** (1)
  - **→ FreshDesk Integration** (1)
  - **→ Zendesk Integration** (2)
  - **→ Seismic Integration** (1)
  - **→ Custom Repository Integration** (2)
- **Integration Hub** (28) - 25 directly here
  - **→ FAQs: Integrations** (3)
- **Third Party Integrations** (5) - 2 directly here
  - **→ Multiformat Integrations** (3)
- **Guidance Analytics** (49) - 2 directly here
  - **→ Whatfix Analytics** (36) - 21 directly here - sub: Identify unique users (3) · New
    Guidance Analytics dashboard experience (12)
  - **→ Custom Analytics** (5)
  - **→ Google Analytics** (6)
- **FAQs** (290)
  - **→ Account Administration** (8)
  - **→ Compliance and Security** (14)
  - **→ Accessibility** (3)
  - **→ CLM Dashboard** (13)
  - **→ Whatfix Content** (102) - sub: General (25) · Flows (29) · Pop-Ups (15) · Visual Editor
    (1) · Beacons (4) · Launchers (3) · Blockers (3) · Content Archival FAQs (7) · Multi format
    (7) · LMS (8)
  - **→ Whatfix Widgets** (41) - sub: Self Help (32) · Task List (8) · Surveys (1)
  - **→ New Visibility Rules** (6)
  - **→ Translation** (12)
  - **→ Deployment and Content Delivery** (27)
  - **→ Auto Testing** (18)
  - **→ Content Aggregation** (19)
  - **→ Integrations** (4)
  - **→ Analytics** (15)
  - **→ New Guidance Analytics Dashboard experience** (8)
- **Troubleshooting** (202)
  - **→ Guidance Analytics** (3)
  - **→ Whatfix Diagnostics in Studio** (17) - 16 directly here - sub: Overview of Instant
    Validation for the new Visibility Rules in Studio (1)
  - **→ Diagnostics** (1)
  - **→ Beacon** (5)
  - **→ Dashboard** (25)
  - **→ Flow** (31) - 27 directly here - sub: Branching in Flows (2) · Free-floating Flow (2)
  - **→ Studio** (12)
  - **→ Smart Tips** (11)
  - **→ Launchers** (3)
  - **→ Blockers** (1)
  - **→ Survey** (3)
  - **→ Miscellaneous Issues** (19)
  - **→ Multi-format Outputs** (6)
  - **→ Pop-up** (11)
  - **→ Self Help** (17) - 12 directly here - sub: QuickRead (5)
  - **→ Improved Self Help** (5)
  - **→ Task List** (5)
  - **→ Translation** (9)
  - **→ Browser Extension** (5)
  - **→ Content Aggregation** (4)
  - **→ Auto Testing** (1)
  - **→ Third Party Integrations** (1)
  - **→ Debugging** (6)
  - **→ Deployment and Delivery** (1)
- **Best Practices** (21)
- **Contact Support** (4)
- **Developer API** (2)
- **Whatfix Release Notes** (55)
- **Whatfix AI Agents** (3)

> Not present as published top-level content in the `studio` workspace: standalone **Product
> Analytics** and **Whatfix Mirror** (separate workspaces — see `product-analytics.md` / `mirror.md`).

---

## Overview

### What is Whatfix?

**Source:** https://support.whatfix.com/docs/en/what-is-whatfix

Whatfix is a **Digital Adoption Platform (DAP)** that helps enterprises onboard, train, and
support the users of their applications. It creates and delivers contextual, customized content —
Flows, help tips, videos, links, and text — as an **in-app** experience, so end users never leave
the application to find information. Whatfix guidance is contextual, interactive, real-time, and
autonomous.

### Where Whatfix is used

**Source:** https://support.whatfix.com/docs/en/what-can-i-do-with-whatfix

Whatfix can be layered on **any web-based enterprise application** (e.g. Salesforce, SAP
SuccessFactors, Oracle HCM Cloud), custom web apps, and consumer-facing websites. It supports
cloud, self-hosted, and on-premise deployment, and separate sandbox vs production instances
(author in staging, deploy to production).

### What Whatfix content is

"Whatfix Content" is the umbrella for everything authors create: **Flows, Smart Tips, Beacons,
Pop-ups, Launchers, Cues, Surveys, Task Lists, Self Help, Blockers**, plus Videos, Images, PDFs,
Articles, and Links — all delivered to end users in-app.

### Whatfix Studio

**Source:** https://support.whatfix.com/docs/en/what-has-changed-on-studio

**Whatfix Studio** is the authoring surface where content creators build DAP content by selecting
elements on the target application and configuring guidance on top of them. On Web it runs as a
browser extension (surface-specific install/capture: see `dap-web.md`).

### Guidance Dashboard

**Source:** https://support.whatfix.com/docs/en/overview-of-the-whatfix-dashboard

The **Guidance Dashboard** (Whatfix Dashboard) is where authors manage, organize, segment, and
publish content and widgets, configure account-level settings, and generate/deploy extensions.

### Content Lifecycle Management (CLM) — dashboard stages

**Source:** https://support.whatfix.com/docs/en/understanding-whatfix-stages

Content moves through three CLM **stages**: **Draft** (create), **Ready** (review), and
**Production** (live to end users). The stage controls visibility and through which published
target content appears. Confirm a draft's intended stage before describing publish behavior — only
**Production** content is live to end users.

### The Whatfix Workflow

**Source:** https://support.whatfix.com/docs/en/understanding-the-whatfix-workflow

End-to-end the workflow is three stages: (1) **choose the deployment method** (Browser Extension or
JS Embed), (2) **create content in Whatfix Studio**, (3) **manage and publish from the Guidance
Dashboard**. Access to Studio + Dashboard and an assigned user role are prerequisites.

### User Roles & Teammates

**Source:** https://support.whatfix.com/docs/en/whatfix-user-roles ·
https://support.whatfix.com/docs/en/add-new-users

The first user in an enterprise becomes the **Account Manager** (admin) and invites others from the
**Users / Teammates** section, assigning roles that determine permissions. Teammates are listed as
**Active** / **Inactive** (deactivating preserves their authored content), and are added as
**Members** (permanent access) or **Guests** (access until a set end date). The four default roles
are Account Manager, Content Manager, Editor, and Translator; **Custom Roles** (GA, Premium only,
enabled via support) let Account Managers combine specific permissions (`use-custom-roles`).
**SCIM** provisions users from your IdP and can map IdP attributes to default or custom roles, and
**Content Ownership Transfer** reassigns content between active teammates without deleting anyone.

---

## Cross-Cutting Rules & Feature Relationships

> Constraints, dependencies, and decisions that span DAP features — the relational nuance that
> makes guidance accurate. Verify the current state before asserting a default; many capabilities
> are Beta / enable-on-request.

### CLM staging & publishing

- Everything lives in **Draft → Ready → Production**; only **Production** is visible to end users.
  Edits to live content require re-publishing to Production. **Selective Publishing** and the
  **Enhanced Publishing Experience** let authors push specific items rather than everything.
- **Segments** of a widget (Self Help/Task List) and individual content can be moved across stages
  independently; "Remove … Segment from Production" exists per content type.

### Roles & access

- **Account Manager** is the first/admin user; only it can invite teammates, set roles, create
  Custom Roles, and transfer content ownership. Studio
  (authoring) vs Dashboard (management) are distinct surfaces — a role may have access to one and
  not the other.

### Beta / enable-on-request features (do NOT assume on)

Many newer capabilities are **Beta or enabled only on explicit customer approval** (contact
`support@whatfix.com`). Confirm before documenting as available: **Blocker** (Web-only Beta),
**Cues** (Beta, incl. Snooze and end-user feedback), **Hub** (unified end-user widget, Beta),
**Improved Self Help** (Beta), **New Pop-up Templates** (Beta), **New Guidance Analytics
Dashboard** (Beta), **GxP re-authentication for publish/unpublish** (Beta), **ScreenSense
AI-powered Element Detection**, **Auto reselect** (Beta), **Auto-heal** (Beta; not on self-hosted
or on-premise), **QuickRead** (Cloud only, prerequisites below), and several **AI authoring**
features. AI-powered Element Detection is **disabled by default**. **Custom Roles** are GA but
Premium-only.

### Element detection & content resilience (key dependency)

- All element-anchored content (Flows, Smart Tips, Beacons, Launchers, Blockers) depends on
  **ScreenSense** element detection. When an app updates and element structure changes, content can
  break — **Auto reselect** and **ScreenSense Auto-heal** (both Beta) reduce manual reselection.
- **Smart Context** reduces the number of manual segments needed by displaying content contextually
  by role/page automatically — a targeting accelerator, not a replacement for Segmentation.

### Visibility Rules: new vs old

- There are **two systems**: the legacy **Display/Visibility Rules** and the **New Visibility Rules
  experience** (more intuitive, expanded triggers, AI authoring). Widgets and content are
  **upgraded** from old to new; both can co-exist during migration. When documenting, match the
  account's experience — don't mix the two vocabularies.

### Deployment & gating

- Two delivery methods on Web: **JS Embed** (preferred when you can modify app source) and
  **Browser Extension** (when you can't). Some apps switch (e.g. extension → JS Embed for SAP
  SuccessFactors). Hosting can be **Whatfix cloud**, **Self-Hosted**, or **On-Premise**. See
  `dap-web.md` for Web specifics.

### When to use which (content-type decisions)

- **Flow vs Smart Tip** — a multi-step walkthrough of a task vs a single contextual tip on one
  element.
- **Beacon vs Smart Tip** — an attention marker that draws the eye to one element vs informational
  hover/i-icon content.
- **Pop-up vs Launcher** — a proactive announcement capped by occurrence vs an always-present
  on-demand trigger button.
- **Cue vs Beacon/Pop-up** — a non-blocking, AI just-in-time next-step nudge vs static
  attention/announcement widgets.
- **Self Help vs Task List** (now unified under **Hub**) — an on-demand searchable help panel vs a
  guided checklist of onboarding/training tasks.
- **Blocker** — when you must *enforce* compliance by disabling/hiding elements, not just guide.

---

## Content Types (the DAP primitives)

### Flows

**Source:** https://support.whatfix.com/docs/en/what-are-flows

**Flows** are a series of steps that walk a user through completing a task or learning an
objective; the steps display as an interactive layer over the application. Related concepts:
**Quick Capture Flows** (GA for all users: perform the task once and Whatfix converts the capture
into a Flow with titles and descriptions, reviewed in a **Live Edit** view), **branched Flows** (multi-level branching),
**free-floating steps** (a step not anchored to an element, used for context), **See live**
(preview/trigger a Flow in the live app), and **Flow on Standby** (fallback shown when a step's
element can't be detected). Flows can be exported in many formats (see Multi-format Outputs).

### Smart Tips

**Source:** https://support.whatfix.com/docs/en/what-are-smart-tips

**Smart Tips** deliver contextual information about a specific UI element — appearing on hover or
as an **i icon** next to the element — for example, to help fill a confusing field. A group of
Smart Tips on a page is a **Smart Tip Collection**. Related: **Smart Tip triggers** (show based on
user actions/input) and **Data Entry Automation** (pre-populate a field value).

### Beacons

**Source:** https://support.whatfix.com/docs/en/what-are-beacons

**Beacons** draw attention to a single important element (e.g. a new feature). Five styles exist
(**Radial, Custom, Ripple, Speckle, Asterisk**), each configurable per Beacon, independent of account-level defaults.
A Beacon can be grouped into a **Beacon Collection** and can attach a Flow, video, or link.

### Pop-ups

**Source:** https://support.whatfix.com/docs/en/what-are-whatfix-pop-ups

**Pop-ups** are informational widgets that appear on the application to convey announcements or
matters needing immediate attention. Built via a **Visual Editor** (drag-and-drop) or one of **6
templates** (**New Pop-up Templates** are Beta; the existing template experience remains), can have a
**Flow attached**, support **Carousel** layouts, scheduling, and **AI-generated** creation.

### Launchers

**Source:** https://support.whatfix.com/docs/en/what-are-launchers

**Launchers** are customizable buttons, placeable anywhere in the application, that trigger
Whatfix content (a Flow, Pop-up, Video, or Link) with a single click; two types, **Icon** and
**Label**. Unlike a Pop-up capped to a
number of appearances, a Launcher is always present so users can pull content on demand. A Launcher
can itself be used as a **Visibility Rule**.

### Cues

**Source:** https://support.whatfix.com/docs/en/what-are-cues

**Cues** are contextual, just-in-time nudges that appear within the user's flow of work to guide
the next step without interrupting or blocking the screen. Cues bring **AI-driven**, proactive
next-action guidance to the exact moment of need (e.g. nudging a user to act on overdue items,
optionally triggering an automated Flow). Cues are organized in **Cue collections**. **Beta**
(enable via your CSM); **Snooze** and **end-user feedback** on Cues are also Beta.

### Surveys

**Source:** https://support.whatfix.com/docs/en/what-are-surveys

**Surveys** collect feedback from end users via in-app questionnaires, with customizable questions
and themes targeted to a specific audience. Variants include **Usability**, **NPS**, and **Quiz**.
A Survey can be attached to other content (Smart Tip, Beacon, Launcher, Pop-up), shared as a public
link, translated, and personalized; responses feed **Survey Analytics**. Several capabilities are
**plan-gated** to Standard and Premium (custom Surveys, the Quiz template, public links, conditions,
branching, qualitative analysis summary, auto translation), so check the plan before documenting
them.

### Task List

**Source:** https://support.whatfix.com/docs/en/what-is-a-task-list

A **Task List** is a widget presenting a list of to-do tasks (e.g. onboarding steps or a training
program) for end users to complete, helping kickstart adoption. Now surfaced as a **tab within the
unified Hub** widget (see below). Tasks can be Flows, links, videos, articles, PDFs, or surveys.

### Blocker

**Source:** https://support.whatfix.com/docs/en/improve-data-accuracy-and-user-compliance-with-blockers

A **Blocker** controls end-user interactions on a page to **enforce process compliance and data
accuracy** — it disables or hides UI elements under defined conditions, preventing incorrect or
incomplete data entry. **Beta, Web-only** (contact support to enable). Use a Blocker when guidance
must be enforced rather than suggested.

### Static Content

**Source:** https://support.whatfix.com/docs/en/creating-link · https://support.whatfix.com/docs/en/creating-text-content

**Static Content** lets authors add **Links, Articles, Images, Videos, and PDFs** from the
Dashboard without selecting elements in Studio. Distinct from **In-app Created Content** (the
element-anchored types above).

---

## End-User Widgets: Self Help & Hub

### Self Help

**Source:** https://support.whatfix.com/docs/en/what-is-self-help

**Self Help** is an in-app widget that surfaces a curated collection of Whatfix content (Flows,
articles, videos, links) as a central, always-available help panel. It supports search, grouping/
nested grouping, content feedback, personalized nudges, ML personalization, and aggregation from
repositories (Confluence, SharePoint, Salesforce, Freshservice, etc.). The browsing surface is the
**Explorer**. **Improved Self Help** (Beta) is a revamped end-user experience that also hosts the
QuickRead and Personalization settings.

### Hub (unified end-user widget)

**Source:** https://support.whatfix.com/docs/en/unified-hub-experience

**Hub** combines **Self Help and Task List into a single widget** behind one **Floating Action
Button (FAB)** — end users access Self Help (Explorer), assigned Tasks, Feedback, and Chatbot from
one panel. **Beta** (contact support). Existing Self Help / Task List authoring is unchanged; Task
List becomes a tab within Hub.

### QuickRead

**Source:** https://support.whatfix.com/docs/en/introduction-to-quickread

**QuickRead** provides **AI-summarized answers** inside Self Help — a concise summary plus a link
to the source article, answering natural-language queries without a page switch. Prerequisites:
at least **50** Whatfix articles or repository links in Production and the **Whatfix Cloud**
deployment; authenticated repositories also need End-user authentication with a matching SSO
(`who-can-be-enabled-with-quickread`). Supports **European languages only**. Once enabled, every
Self Help segment gets it; has its own analytics. (Part of the Guidance Agents
family below.)

---

## Targeting & Delivery

### Segmentation

**Source:** https://support.whatfix.com/docs/en/what-is-segmentation

**Segmentation** controls which content is shown to which users on which pages — targeting Flows
and widgets (Self Help, Task List) by conditions such as user login, URL, on-screen elements, or a
mix of criteria. Up to **75 segments per widget** by default. When two widgets compete, **Widget
priority** (GA) on the Dashboard sets the order they appear in (`set-widget-priority-on-whatfix-dashboard`).

### Tags

**Source:** https://support.whatfix.com/docs/en/what-are-tags

A **Tag** is a label that organizes content into categories and helps identify a page so the right
Whatfix content displays on it. **Page Tags** and **Role Tags** drive page-based and role-based
segmentation; **Global Tags** apply across the account. **Auto Tags** are available only where
Smart Context is enabled, and a Page Tag can override an Auto Tag.

### Visibility Rules (new & old)

**Source:** https://support.whatfix.com/docs/en/understand-visibility-rules-20 (widgets) ·
https://support.whatfix.com/docs/en/understand-advanced-visibility-rules-for-content (content) ·
https://support.whatfix.com/docs/en/supported-operators-for-visibility-rules (operators)

**Visibility Rules** control **where, when, and to whom** Whatfix widgets and content display. The
**New Visibility Rules experience** supersedes the legacy Display/Visibility Rules with a more
intuitive interface, expanded triggers (URL properties, other-element conditions, window variables,
attributes, dates, events, intent-matching text), AI authoring, and per-step control for Flows.
Rules group with **AND/OR**. Widgets and content are **upgraded** from old to new; both can
co-exist during migration.

### User Attributes

**Source:** https://support.whatfix.com/docs/en/user-attributes

**User Attributes** are user properties (role, department, geography, SSO-provided values) used to
target and segment content and to break down analytics.

### Custom Variables

**Source:** https://support.whatfix.com/docs/en/create-a-variable

**Custom Variables** personalize Whatfix content (e.g. inject a user's name) and can be used in
conditions. Configured under Configure Whatfix Content.

### User & Locale Identification

**Source:** https://support.whatfix.com/docs/en/configure-user-identification-rules

**User Identification rules** tell Whatfix who the end user is (custom rules, pre-configured apps,
or fetched/processed info); **Locale identification** maps language codes to locale rules.
Identification underpins unique-user analytics and personalized targeting.

---

## Element Detection & Resilience

### ScreenSense

**Source:** https://support.whatfix.com/docs/en/screensense-ai-powered-ed

**ScreenSense** is Whatfix's patented **element-detection** engine — it captures and remembers UI
elements at authoring time so guidance anchors correctly every time. **ScreenSense: AI-powered
Element Detection** augments it with AI for hard-to-resolve elements; it is **disabled by default**
and enabled only on explicit customer approval.

### Smart Context

**Source:** https://support.whatfix.com/docs/en/smart-context

**Smart Context** removes the need to manually create many segments — it displays the right content
contextually to different roles/pages automatically (e.g. a 5-page, 2-role app would otherwise need
10 manual segments). A targeting accelerator layered on Segmentation.

### Auto reselect

**Source:** https://support.whatfix.com/docs/en/element-reselection-automation

**Auto reselect** (Beta) automatically re-selects elements after an application update for content
that requires element selection (Flow steps, Smart Tips, Beacons, etc.), avoiding manual rework
when the underlying element structure changes.

### ScreenSense Auto-heal

**Source:** https://support.whatfix.com/docs/en/screensense-auto-heal

**Auto-heal** (Beta) automatically recovers content failures when app changes alter the elements
that content is bound to. Supported for Flows, Smart Tips, Beacons, Launchers, Blockers, and User
Actions. **Not supported on self-hosted or on-premise deployments.**

---

## AI Capabilities

### Whatfix Authoring Agents

**Source:** https://support.whatfix.com/docs/en/whatfix-authoring-agents

**Authoring Agents** create fully configured content from natural-language prompts — Pop-ups,
Flows, and Visibility Rules — including AI CSS customization and multi-template AI Pop-ups, ready to
review and configure.

### Whatfix Guidance Agents

**Source:** https://support.whatfix.com/docs/en/whatfix-guidance-agents

**Guidance Agents** deliver contextual, AI-powered support in the flow of work — chiefly
**QuickRead**, which surfaces concise answers from your documentation directly in the Self Help
widget without a page switch.

### Whatfix Insights Agents

**Source:** https://support.whatfix.com/docs/en/whatfix-insights-agents

**Insights Agents** turn behavior, feedback, and performance data into actionable insights via
natural-language questions through **Ask Whatfix AI** (returns Trend/Funnel/Journey charts;
deeper reasoning is now built in, so there is no separate Deep think toggle). These bridge into Product Analytics (see
`product-analytics.md`).

---

## Authoring Lifecycle (overviews)

> Peripheral to core authoring — covered as overviews; retrieval has the detailed steps.

### Translations & Multi-language

**Source:** https://support.whatfix.com/docs/en/translating-whatfix-content-1 ·
https://support.whatfix.com/docs/en/languages-supported-by-whatfix

Translate content into other languages without recreating it. A **primary language** is set for
auto-translation; translate via the **Whatfix UI**, **XLIFF**, **Excel**, or **Property files**, or
a **Custom Translation Tool**. Translation has a **status** (in-sync / out-of-sync) and custom-label
renaming. Whatfix can auto-detect the app's language.

### Multi-format Outputs

**Source:** https://support.whatfix.com/docs/en/scorm-package-export ·
https://support.whatfix.com/docs/en/xapi-package-export ·
https://support.whatfix.com/docs/en/whatfix-videos-1

A Flow can be repurposed as a **Video** (incl. AI voiceover), **Slideshow**, **PDF**, **ODF**,
**Link**, **article embed**, **Live Tour**, or exported as a **SCORM / xAPI** package for an LMS.

### Content Archival & Versioning

**Source:** https://support.whatfix.com/docs/en/archive-whatfix-content-or-widgets ·
https://support.whatfix.com/docs/en/content-versioning

**Archive** content/widgets to retire without deleting (view/restore/copy later; affects analytics,
translations, Auto Testing, and linked content). **Content Versioning** tracks revisions of a piece
of content.

### Testing & Diagnostics

**Source:** https://support.whatfix.com/docs/en/what-is-a-test-case-1 ·
https://support.whatfix.com/docs/en/create-a-test-suite ·
https://support.whatfix.com/docs/en/troubleshoot-flows-using-diagnostics

**Auto Testing** verifies Flows still work at regular intervals: a **Test Case** captures the inputs
a Flow needs; **Test Suites** group and schedule cases and produce reports. **Whatfix Diagnostics**
(in Studio) identifies why a piece of content (Flow, Smart Tip, Beacon, Pop-up, Launcher, Self Help,
Task List, Cue, Visibility Rule) isn't behaving and gives actionable, non-technical fixes, including
**Live Edit** and CSS-selector repair.

---

## Analytics (overview)

> DAP **Guidance Analytics** is distinct from the standalone **Product Analytics** product (its own
> workspace — see `product-analytics.md`). Covered here as an overview.

**Source:** https://support.whatfix.com/docs/en/enable-whatfix-analytics-to-capture-engagement-data ·
https://support.whatfix.com/docs/en/overview-of-the-new-guidance-analytics-dashboard-experience

**Whatfix (Guidance) Analytics** reports usage and engagement for all Whatfix content in visual
form — per-content dashboards (Flow, Smart Tip, Beacon, Pop-up, Launcher, Self Help, Task List,
Survey), an **Analytics Summary**, unique-users/engagement data, CLM-stage filtering, and audit
logs. A **New Guidance Analytics Dashboard** experience (Beta) exists alongside the classic one;
it does not yet support Survey Analytics. **Custom
Analytics** integrates external tools (Adobe/Omniture, Matomo, Google Analytics, API export).

---

## Integrations (overview)

### Integration Hub

**Source:** https://support.whatfix.com/docs/en/integration-hub-overview-1

The **Integration Hub** (part of Whatfix's Open Ecosystem Platform) exchanges data and attribute
streams with other products (20+ integrations: Amplitude, Confluence, FullStory, Google
Analytics/Sheets, Power BI, Workday, ServiceNow, Salesforce, etc.) and provides **Enterprise
Attributes** for content segmentation.

### Content Aggregation

**Source:** https://support.whatfix.com/docs/en/view-content-repository-links-on-the-dashboard

**Content Aggregation** pulls external repository content (SharePoint, OneDrive, ServiceNow,
Freshservice, Confluence, Salesforce, Zendesk, Seismic, ShareFile, or a custom integration) and
surfaces it in Self Help, with configurable sync frequency and status reporting.

---

## FAQs & Troubleshooting (folded)

> The workspace has large **FAQs** (290) and **Troubleshooting** (202) categories plus per-feature
> **Best Practices** (21). Summarized here by theme; retrieve the specific article for an answer.

- **FAQs themes** — Account Administration; Compliance & Security; CLM Dashboard; Whatfix Content
  (General, Flows, Pop-ups, Beacons, Launchers, Blockers, Visual Editor, Archival, Multi-format,
  LMS); Self Help & QuickRead; Task List; Surveys; New Visibility Rules; Translation; Deployment &
  Content Delivery; Auto Testing; Content Aggregation; Integrations; Analytics. Common items:
  account ID lookup, character limits, trusted Whatfix domains/IPs to whitelist, single-page-app
  support, "What is Smart Context?", how content displays, deployment-method differences.
- **Troubleshooting themes** — Studio install/visibility; Dashboard publish/login errors; Flow
  failures (CSS selector failed, element not found, display rules failed, Auto Step incomplete);
  Smart Tip / Beacon / Launcher / Pop-up positioning & visibility; Self Help / Improved Self Help /
  QuickRead not showing; Task List; Translation; Browser Extension (install blocked by policy,
  permissions, update issues); Content Aggregation; **Whatfix Diagnostics** per content type; and a
  **Debugging** set (verify Smart Context, identify CSS selector / tags, debug a Flow failure).
- **Best Practices** exist per feature (Flows, Tooltips, Smart Tips, Beacons, Pop-ups, Launchers,
  Surveys, Task Lists, Self Help, Segmentation, Visibility Rules, Studio, Dashboard, Static Content,
  Content Organization/Governance, Publishing, Icon Library, Content Aggregation).

---

## Glossary

**Source:** https://support.whatfix.com/docs/en/whatfix-glossary

| Term | Meaning |
|---|---|
| **DAP** | Digital Adoption Platform — the Whatfix core product. |
| **Whatfix Content** | Umbrella for all authored items (Flows, Smart Tips, Beacons, Pop-ups, Launchers, Cues, Surveys, Task Lists, Self Help, Blockers, Videos, Static Content). |
| **Whatfix Studio** | The authoring surface for creating content on an application. |
| **Guidance Dashboard** | Where content is managed, segmented, and published. |
| **CLM / Stages** | Content Lifecycle Management: Draft → Ready → Production. |
| **Flow** | A multi-step interactive walkthrough layered over the app. |
| **Smart Tip** | Contextual tip on a specific element (hover or i-icon). |
| **Beacon** | Attention-drawing marker on a single element. |
| **Pop-up** | Informational widget for announcements / immediate attention. |
| **Launcher** | Always-present button that triggers content on demand. |
| **Cue** | AI-driven, just-in-time, non-blocking next-step nudge (Beta). |
| **Survey** | In-app questionnaire (Usability / NPS / Quiz) for feedback. |
| **Task List** | Widget listing onboarding/training tasks; now a Hub tab. |
| **Self Help** | In-app panel surfacing curated help content; browsing via Explorer. |
| **Hub** | Unified end-user widget combining Self Help + Task List (Beta). |
| **QuickRead** | AI-summarized answers inside Self Help. |
| **Blocker** | Enforces compliance by disabling/hiding UI elements (Web-only Beta). |
| **Segmentation** | Targeting content to specific users/pages by rules. |
| **Tag** | Label that categorizes content and identifies a page (Page/Role/Global). |
| **Visibility Rules** | Where/when/to-whom rules for widgets & content (New vs legacy). |
| **ScreenSense** | Whatfix's element-detection engine (AI-augmented, opt-in). |
| **Smart Context** | Automatic contextual targeting, reducing manual segments. |
| **Auto reselect / Auto-heal** | Automatic recovery of element references after app changes (Beta). |
| **Guidance Analytics** | Usage/engagement analytics for Whatfix content (distinct from Product Analytics). |
| **Integration Hub** | Data/attribute exchange with external products. |
| **AI Agents** | Authoring / Guidance / Insights agents (natural-language content, support, analytics). |
