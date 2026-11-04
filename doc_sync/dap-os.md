# Whatfix DAP on OS — Surface Delta Reference

> Model for **DAP on OS** — Whatfix's **system-level desktop application** ("Whatfix Hub") that gives
> end users one place on their desktop to find organizational content, documents, and Whatfix content
> **across all their applications**, plus push **communications** (pop-ups, desktop wallpaper,
> notifications). This is a DELTA on top of `dap-core.md` for shared DAP philosophy (in-app, no-code,
> CLM staging, roles, segmentation, content aggregation, Integration Hub, analytics) — but DAP on OS
> has a DISTINCT model: it **surfaces and communicates content at the OS level**, it does NOT author
> element-anchored in-app guidance (Flows/Smart Tips/Beacons) on a target app's UI.
>
> **DAP on OS ≠ DAP for Desktop.** Two DISTINCT products in separate D360 workspaces:
> **DAP on OS** = the `hub` workspace (this file; `/hub/docs/en/…`), a system-level app (Explorer +
> Communications). **DAP for Desktop** = the `desktop` workspace (`dap-desktop.md`;
> `/desktop/docs/en/…`), DAP latched onto specific desktop *applications* (Desktop Studio + Player,
> Flows/Smart Tips/Beacons). Do not conflate. Verified against the live `hub` workspace on 2026-09-25
> (Release Notes / Contact Support excluded). Concepts only — follow the
> `Source:` link (canonical `/hub/docs/en/` form), also a valid **cross-link** target.

## Table of Contents

- [DAP on OS Content Map (published IA snapshot)](#dap-on-os-content-map-published-ia-snapshot)
- [What DAP on OS is](#what-dap-on-os-is)
- [Cross-Cutting Rules & OS Relationships](#cross-cutting-rules--os-relationships)
- [Install & access (the Hub app)](#install--access-the-hub-app)
- [End-user surfaces: Explorer, Communications, Task List, Feedback](#end-user-surfaces-explorer-communications-task-list-feedback)
- [Content for DAP on OS](#content-for-dap-on-os)
- [Targeting: Advanced Visibility Rules & Segmentation](#targeting-advanced-visibility-rules--segmentation)
- [Content Aggregation & Integrations](#content-aggregation--integrations)
- [Analytics on DAP on OS](#analytics-on-dap-on-os)
- [FAQs & Best Practices (folded)](#faqs--best-practices-folded)
- [Glossary (DAP on OS)](#glossary-dap-on-os)

---

## DAP on OS Content Map (published IA snapshot)

> A snapshot of the Document360 category structure and published article inventory for the `hub`
> workspace (187 published articles when it was taken). Use it to see where a feature is documented
> and which categories are likely to hold articles a change affects. It is not refreshed
> automatically, so the live workspace may have moved on since; the knowledge index (kb_index.py) is
> the up-to-date source for what is published now.

- **Whatfix DAP on OS Overview** (4) - What is DAP on OS? · Get Started with DAP on OS ·
  Pre-requisites to work with DAP on OS · DAP on OS Glossary
- **Install DAP on OS** (5) - How to start and stop Whatfix DAP on OS? · Access Hub · Quit Hub ·
  Uninstall DAP on OS
  - **→ Choose an installation method** (1) - Mass Deployment of DAP on OS
- **DAP on OS Administration** (11) - Generate the API Token
  - **→ User Management** (7)
  - **→ Security and Compliance** (3) - Enforce Password Policies · End-user authentication ·
    Whatfix Service Level Agreement (SLA)
- **Create content and widgets for DAP on OS** (66) - Organization Wide Search · Hub
  Customizations · Enable Preview Mode
  - **→ Advanced Visibility Rules** (4) - Understand Advanced Visibility Rules · Set when your
    widget appears · Set who can see your widget · Attributes in Advanced Visibility Rules
  - **→ Create content for DAP on OS** (5)
  - **→ Translations** (20) - Overview of Translations · Add a new language for translation ·
    Languages Supported by Whatfix · Change the primary language for translating content - sub:
    Translate Whatfix Content (12) · Translation Status (2) · Custom Translation Tool (2)
  - **→ Create Explorer** (11) - Create Explorer · Configure Self Help - sub: Content listing in
    Explorer (3) · Search in Explorer (4) · QuickRead for DAP on OS (2)
  - **→ Create Task List** (3) - Create Task List · Nudge users to complete a task · Content
    Grouping in Task list
  - **→ Configure Feedback** (2) - Configure feedback in DAP on OS · Email notifications for
    feedback
  - **→ Create Communications** (11) - sub: Content Author (11)
  - **→ Segmentation** (5) - sub: Content Segmentation (5)
  - **→ Deployment and Delivery** (2) - Push Whatfix contents and widgets to production · What are
    the trusted Whatfix domains to whitelist?
- **End-user experience** (3)
  - **→ Communications** (3) - sub: End User (3)
- **Content Aggregation** (21) - Content Aggregation Process
  - **→ Custom Repository** (8)
  - **→ Salesforce Integration** (2) - File integration for Salesforce · Integrate Salesforce
    Repository
  - **→ SharePoint Integration** (2) - Generate ClientID and SecretKey for SharePoint Integration
    · Generate Information for SharePoint Subsite Integration
  - **→ OneDrive Integration** (2) - Integrate Specific Content from OneDrive Repository ·
    OneDrive Integration Process
  - **→ ServiceNow Integration** (1) - Generate ServiceNow Credentials
  - **→ FreshDesk Integration** (1) - Integrate Freshdesk repository
  - **→ Freshservice Integration** (1) - Generate Credentials for Freshservice Integration
  - **→ Confluence Repository Integration** (1) - Generate Credentials for Confluence Integration
  - **→ Zendesk Integration** (2) - Generate Credentials for Zendesk Integration · Integrate
    Zendesk Repository
- **Integrations** (25)
- **Analytics** (27)
  - **→ Guidance Analytics** (5) - sub: Whatfix Guidance Analytics for DAP on OS (5)
  - **→ Product Analytics** (22) - Get Analytics Data across CLM Stages · Enable Product Analytics
    for your account - sub: Analyze (20)
- **FAQs** (16)
  - **→ General** (13)
  - **→ Deployment and Delivery** (1) - What are the trusted Whatfix domains to whitelist?
  - **→ User Authentication** (2) - What data does DAP on OS collect and store? · How is user
    authentication done for DAP on OS?
- **Best Practices** (8)
- **Release Notes** (1) - Q4 R2 2024 Release

---

## What DAP on OS is

**Source:** https://support.whatfix.com/hub/docs/en/what-is-dap-on-os

**DAP on OS** is a **system-level application** (installed on the desktop, the "Whatfix Hub") that
lets end users access organizational documents, resources, and Whatfix content **across multiple
applications from one place** on their desktop — reducing app-switching and surfacing the right
content and notifications at the OS level. Its value is **centralized content access + proactive
communication**, not authoring guidance on a specific app's UI elements.

**Source:** https://support.whatfix.com/hub/docs/en/getting-started-with-dap-on-os

---

## Cross-Cutting Rules & OS Relationships

> The relational nuance specific to DAP on OS. Confirm before asserting a default; several features
> are Beta / enable-on-request.

- **System-level app, not an in-app overlay on one application.** DAP on OS runs as a desktop app
  ("Whatfix Hub") reachable via a desktop **Pin**, the **Taskbar (Windows) / Dock (macOS)**, or
  Spotlight; it floats over whatever window the user is in. Supported on **Windows and macOS**.
- **It surfaces/communicates content; it does not author element-anchored guidance.** Content on DAP
  on OS is **Links, Articles, Videos, Images, and Flows-as-links** (native Flows/Smart Tips/Beacons
  are NOT created here — "DAP on OS supports Flows as link only"). For element-anchored guidance on a
  desktop app, that's **DAP for Desktop** (`dap-desktop.md`); on the web, Whatfix Web.
- **Independent of application-level DAP.** You can run DAP on OS without app-level DAP (see FAQs:
  "Do you need application-level DAP as well if you have DAP on OS?"). The two are complementary.
- **End-user surfaces:** **Explorer** (content access/search), **Communications** (Pop-ups, Desktop
  Wallpaper, Notifications), **Task List**, and **Feedback** — all within the Hub panel.
- **Same management spine as core:** Whatfix Guidance Dashboard, **Draft → Ready → Production**
  staging, roles, segmentation, content aggregation, Integration Hub.
- **Beta / enable-on-request:** **Desktop Wallpaper Communication**, **Advanced Visibility Rules**
  (selected customers), **Organization Wide Search** (needs an Organization ID linking multiple ENTs).
- **Embedded analytics:** Guidance Analytics for DAP on OS (Explorer/Pop-up/Feedback) **plus** an
  embedded Product Analytics (Trend Insights, Dashboards) — see `product-analytics.md` for PA concepts.

---

## Install & access (the Hub app)

**Source:** https://support.whatfix.com/hub/docs/en/pre-requisites-to-work-with-whatfix-hub ·
https://support.whatfix.com/hub/docs/en/access-dap-on-os

Prerequisites: **whitelist trusted Whatfix domains** + **install the DAP on OS app**. After install,
an interactive **Pin** icon appears on the desktop; users also access the Hub from the **Taskbar /
Dock** or Spotlight, and after quitting it from the Taskbar/Dock it stays active in the **System Tray
(Windows) / Menu Bar (macOS)**. **Start/stop** differs by OS (macOS: Applications/Spotlight → WhatFixHub, Quit
from the menu bar; Windows: from the Player install dir). **Mass Deployment** places the app at
system level (Program Files / Applications) and installs per-user on first sign-in.

- Start/stop: https://support.whatfix.com/hub/docs/en/how-to-start-and-stop-whatfix-dap-on-os
- Mass Deployment: https://support.whatfix.com/hub/docs/en/mass-deployment-of-dap-on-os

---

## End-user surfaces: Explorer, Communications, Task List, Feedback

### Explorer

**Source:** https://support.whatfix.com/hub/docs/en/create-and-configure-explorer

**Explorer** is the DAP-on-OS content-access surface — end users open it on the desktop to find
content specific to their organization across applications (support articles, Confluence docs,
compliance info, Whatfix content). It is configured as **Self Help segments**, with content listing,
grouping, search, and **QuickRead** (AI-summarized answers,
https://support.whatfix.com/hub/docs/en/enable-or-disable-quickread). **Organization Wide Search**
(https://support.whatfix.com/hub/docs/en/organization-wide-search) searches across multiple
Enterprises (ENTs) under one Organization ID (created or linked via support); **not supported in
Export Mode** of deployment.

### Communications (Pop-ups, Desktop Wallpaper, Notifications)

**Source:** https://support.whatfix.com/hub/docs/en/what-are-whatfix-pop-ups

**Communications** push proactive messages at the OS level:
- **Pop-ups** — information widgets (six templates; Visual Editor; images; delivery mode; visibility
  rules) for announcements, updates, alerts. Authored under Create Communications > Content Author.
- **Desktop Wallpaper Communication** (Beta) — deliver critical updates to end users' desktop
  lock/home screens. https://support.whatfix.com/hub/docs/en/desktop-wallpaper-communication
- **Notifications** — a Hub component listing all notified communications, with read/unread states.
  https://support.whatfix.com/hub/docs/en/notifications-1

### Task List & Feedback

**Source:** https://support.whatfix.com/hub/docs/en/create-task-list ·
https://support.whatfix.com/hub/docs/en/customize-the-feedback-form

**Task List** presents to-do/onboarding tasks with self-tracked progress and nudges. **Feedback** is
a configurable panel (collect-feedback toggle, customizable form, email notifications).

---

## Content for DAP on OS

**Source:** https://support.whatfix.com/hub/docs/en/embed-flows-as-links

Content surfaced on DAP on OS is **Static Content** — **Links, Articles, Videos, Images** — plus
**Flows as links** (Flows authored elsewhere, added by link; DAP on OS supports Flows **as link
only**). **Translations** are supported (primary language, UI/XLIFF/Excel/Property files, status,
custom tool). **Hub Customizations** and **Preview Mode** apply.

- Customizations: https://support.whatfix.com/hub/docs/en/dap-on-os-customization
- Preview Mode: https://support.whatfix.com/hub/docs/en/enable-preview-mode-for-dap-on-os

---

## Targeting: Advanced Visibility Rules & Segmentation

**Source:** https://support.whatfix.com/hub/docs/en/understand-widget-behavior-with-advanced-visibility-rules ·
https://support.whatfix.com/hub/docs/en/segmentation-attributes

**Advanced Visibility Rules** determine where, when, and to whom widgets (Self Help/Explorer, Task
List, Pop-ups) appear — by attributes, user/role, and conditions (selected customers). **Content
Segmentation** uses **Segmentation Attributes** (Role Tags, Other Tags, User Attributes, Enterprise
Attributes), and supports **Google Sheets** and **Azure AD role-based** segmentation plus **User ID
identification** for DAP on OS.

---

## Content Aggregation & Integrations

**Source:** https://support.whatfix.com/hub/docs/en/content-aggregation-process ·
https://support.whatfix.com/hub/docs/en/integration-hub-overview

**Content Aggregation** crawls external repositories (Custom, SharePoint, OneDrive, ServiceNow,
Freshservice, Confluence, Salesforce, Zendesk, FreshDesk) and surfaces them in Explorer (repos with
MFA unsupported; >10 MB per link not crawled). **Integration Hub** (~25 integrations: Amplitude,
Power BI, Workday, Google Analytics/Sheets, Salesforce, Azure AD, etc.) exchanges data/attributes,
including **User/Enterprise Attributes** for segmentation.

---

## Analytics on DAP on OS

**Source:** https://support.whatfix.com/hub/docs/en/analytics-summary

DAP on OS embeds **two** analytics surfaces:
- **Guidance Analytics for DAP on OS** — Summary (unique users shown Hub, engagement), **Explorer
  Analytics** (https://support.whatfix.com/hub/docs/en/explorer-analytics), **Pop-up Analytics**,
  **Feedback Analytics**, downloadable summary report.
- **Product Analytics** (embedded) — Trend Insights, Dashboards, CLM-stage data; enable via
  https://support.whatfix.com/hub/docs/en/enable-product-analytics-for-your-account. For PA concepts,
  see **`product-analytics.md`**.

---

## FAQs & Best Practices (folded)

> The workspace has **FAQs** (16) and **Best Practices** (8); summarized — retrieve the specific
> article for an answer.

- **FAQs themes** — General (operating systems supported, content types supported, QuickRead content
  types, "Can we launch Flows from DAP on OS?", "Does DAP on OS support Desktop content or just Web?",
  "Do you need application-level DAP as well?", two-Self-Help-widgets scenario, task due dates, text
  snippets vs tasks, integrations offered); Deployment & Delivery (trusted domains); **User
  Authentication** (what data DAP on OS collects/stores; how auth is done).
- **Best Practices** — Content Aggregation, Content Governance, Dashboard, Guidance Analytics,
  Pushing to Production, Pop-ups, Self Help, Task List.

---

## Glossary (DAP on OS)

**Source:** https://support.whatfix.com/hub/docs/en/whatfix-hub-glossary

| Term | Meaning |
|---|---|
| **DAP on OS / Whatfix Hub** | System-level desktop app surfacing org + Whatfix content across apps. |
| **Pin** | The interactive desktop icon to open the Hub over any window. |
| **Explorer** | The Hub content-access/search surface (configured as Self Help segments). |
| **Organization Wide Search** | Search content across multiple ENTs under one Organization ID. |
| **Communications** | OS-level messaging: Pop-ups, Desktop Wallpaper, Notifications. |
| **Desktop Wallpaper Communication** | Deliver updates to desktop lock/home screens (Beta). |
| **Notifications** | Hub component listing all notified communications (read/unread). |
| **Task List** | To-do/onboarding tasks with self-tracked progress, in the Hub. |
| **Flows as links** | Flows surfaced by link (DAP on OS supports Flows as link only). |
| **Advanced Visibility Rules** | Where/when/to-whom targeting for Hub widgets (selected customers). |
| **Segmentation Attributes** | Role/Other Tags, User/Enterprise Attributes for targeting. |
| **Mass Deployment** | System-level install of the DAP on OS app (per-user on first sign-in). |
| **DAP for Desktop** | SEPARATE product (`desktop` workspace) — DAP on native desktop *applications*. |
