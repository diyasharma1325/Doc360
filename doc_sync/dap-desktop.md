# Whatfix DAP for Desktop — Surface Delta Reference

> Model for the Whatfix Digital Adoption Platform delivered over **native desktop applications**
> (Windows desktop apps — e.g. SAP GUI, a Win32/Java client) via installable Whatfix apps. This is a
> DELTA on top of `dap-core.md` for the shared DAP primitives (Flows, Smart Tips, Beacons, Pop-ups,
> Self Help, Task List, Segmentation, Tags, Translations, Multi-format Outputs, Content Aggregation,
> Integration Hub, QuickRead) — those concepts are NOT repeated here; this file covers what is
> DIFFERENT on the desktop surface: the installable **Desktop Studio + Desktop Player** apps, the
> **CLM Desktop Dashboard**, multi-application/multi-window delivery, prerequisites/system
> requirements, and desktop-specific behaviors (offline, cross-application Flows).
>
> **DAP for Desktop ≠ DAP on OS.** They are TWO DISTINCT products in separate D360 workspaces:
> **DAP for Desktop** = the `desktop` workspace (this file; `/desktop/docs/en/…`), DAP latched onto
> specific desktop *applications*. **DAP on OS** = the `hub` workspace (`dap-os.md`;
> `/hub/docs/en/…`), the system-level product whose end-user surface is **Explorer + Communications**.
> Don't conflate them. Verified against the live `desktop` workspace on 2026-09-25
> (Release Notes / Contact Support excluded). Concepts only — follow the `Source:` link
> (canonical `/desktop/docs/en/` form), also a valid **cross-link** target.

## Table of Contents

- [DAP for Desktop Content Map (published IA snapshot)](#dap-for-desktop-content-map-published-ia-snapshot)
- [What DAP for Desktop is](#what-dap-for-desktop-is)
- [Cross-Cutting Rules & Desktop Relationships](#cross-cutting-rules--desktop-relationships)
- [The desktop apps: Studio & Player](#the-desktop-apps-studio--player)
- [Prerequisites & system requirements](#prerequisites--system-requirements)
- [CLM Desktop Dashboard](#clm-desktop-dashboard)
- [Multi-application delivery behaviors](#multi-application-delivery-behaviors)
- [Content types on Desktop (deltas)](#content-types-on-desktop-deltas)
- [Self Help & Explorer on Desktop](#self-help--explorer-on-desktop)
- [Publishing, hosting & deployment](#publishing-hosting--deployment)
- [Analytics on Desktop](#analytics-on-desktop)
- [FAQs, Troubleshooting & Best Practices (folded)](#faqs-troubleshooting--best-practices-folded)
- [Glossary (Desktop)](#glossary-desktop)

---

## DAP for Desktop Content Map (published IA snapshot)

> A snapshot of the Document360 category structure and published article inventory for the `desktop`
> workspace (550 published articles when it was taken). Use it to see where a feature is documented
> and which categories are likely to hold articles a change affects. It is not refreshed
> automatically, so the live workspace may have moved on since; the knowledge index (kb_index.py) is
> the up-to-date source for what is published now.

- **Whatfix Desktop Overview** (16) - 12 directly here
  - **→ The CLM Desktop Dashboard** (4)
- **Whatfix Desktop Apps** (7) - 1 directly here
  - **→ Whatfix Desktop Studio** (3)
  - **→ Whatfix Desktop Player** (3)
- **Whatfix Desktop Administration** (12)
  - **→ User Management - Whatfix Desktop** (6)
  - **→ Security and Compliance - Whatfix Desktop** (6)
- **Create Whatfix Desktop Content** (149) - 3 directly here
  - **→ Flows - Whatfix Desktop** (29) - 27 directly here - sub: Free-floating steps in Flows (2)
  - **→ Smart Tips- Whatfix Desktop** (13)
  - **→ Beacons - Whatfix Desktop** (9)
  - **→ Pop-Ups** (30) - 21 directly here - sub: Embed Videos in Pop-ups (9)
  - **→ Static Content - Whatfix Desktop** (5)
  - **→ Multi Format Outputs - Whatfix Desktop** (21) - 2 directly here - sub: Whatfix PDF Export
    (3) · Whatfix ODF Export (2) · Whatfix Videos (10) · Whatfix Slideshows (3) · Whatfix Links
    (1)
  - **→ Desktop Translation** (26) - 10 directly here - sub: Translate Whatfix Content (12) ·
    Translation Status (2) · Custom Translation Tool (2)
  - **→ Icon Library** (2)
  - **→ Configure Whatfix Desktop Content** (6)
  - **→ Content Archival - Whatfix Desktop** (3)
  - **→ Manage Whatfix Content and Widgets** (2)
- **Organize Whatfix Desktop Content** (62) - 1 directly here
  - **→ Segmentation** (5)
  - **→ Configure Self Help** (50) - 37 directly here - sub: QuickRead - Summarized Answers in
    Self Help (4) · Explorer (9)
  - **→ Configure a Task list** (6)
- **Publish Whatfix Desktop Content** (6) - 4 directly here
  - **→ Self Hosting Whatfix Desktop content** (2)
- **Content Aggregation for Desktop** (24) - 1 directly here
  - **→ Custom Repository** (9)
  - **→ SharePoint Integration** (3)
  - **→ OneDrive Integration** (2)
  - **→ ServiceNow Integration** (1)
  - **→ Freshservice Integration** (1)
  - **→ Confluence Repository Integration** (1)
  - **→ Salesforce Integration** (2)
  - **→ Sharefile Integration** (1)
  - **→ FreshDesk Integration** (1)
  - **→ Zendesk Integration** (2)
- **Integration Hub for Desktop** (25)
- **Guidance Analytics for Whatfix Desktop** (18)
  - **→ Whatfix Analytics** (18)
- **Product Analytics for Whatfix Desktop** (55)
  - **→ Track** (13) - sub: Events (13)
  - **→ Analyze** (42) - sub: Funnels (8) · Trend Insights (8) · Dashboards (11) · User Journeys
    (5) · Cohorts (10)
- **Troubleshooting - Whatfix Desktop** (58)
  - **→ Installation** (9) - 4 directly here - sub: Whatfix Player (5)
  - **→ General** (3)
  - **→ Flows** (4)
  - **→ Dashboard** (14)
  - **→ Beacons** (3)
  - **→ Widgets** (4)
  - **→ User Roles** (1)
  - **→ Smart Tips** (5)
  - **→ QuickRead** (2)
  - **→ Improved Self Help** (5)
  - **→ Whatfix Diagnostics** (8)
- **Whatfix Desktop FAQs** (77)
  - **→ Analytics** (3)
  - **→ Content Aggregation** (1)
  - **→ Compliance and Security** (7)
  - **→ CLM Dashboard** (5)
  - **→ Deployment and Content Delivery** (10)
  - **→ General** (9)
  - **→ Product Analytics** (5) - sub: Schedule Insight reports (5)
  - **→ QuickRead** (15)
  - **→ Whatfix Content** (19) - 13 directly here - sub: Content Archival (6)
  - **→ Create Pop-up with AI** (3)
- **Best Practices - Whatfix Desktop** (13)
- **Release Notes - Whatfix Desktop** (24)
- **Whatfix AI Agents for Desktop** (3)
- **Contact Support** (1)

---

## What DAP for Desktop is

**Source:** https://support.whatfix.com/desktop/docs/en/what-is-whatfix-desktop-1 ·
https://support.whatfix.com/desktop/docs/en/what-can-you-do-with-whatfix-desktop

**DAP for Desktop** (Whatfix Desktop) layers Whatfix guidance **over native desktop applications** —
onboarding, training, and in-app help displayed as a layer on the desktop app, the desktop analog of
Whatfix Web. The same DAP value (contextual, no-code, in-app) applies; the difference is the
**delivery surface**: a native desktop application rather than a web page, reached via installable
Whatfix apps rather than a browser extension or JS embed.

**Source:** https://support.whatfix.com/desktop/docs/en/features-available-in-whatfix-desktop

---

## Cross-Cutting Rules & Desktop Relationships

> The relational nuance specific to the desktop surface. Confirm before asserting a default; several
> behaviors are enable-on-request.

- **Two installable apps, not a browser extension.** Authoring uses the **Whatfix Desktop Studio**
  app; end-user delivery uses the **Whatfix Desktop Player** app. Both are installed on the machine
  (user-level or system-level). This replaces the Web Studio browser extension / JS Embed model.
- **Multi-application, multi-window.** One Desktop Studio authors content across **multiple desktop
  applications**; widgets latch onto the application (or window) **in focus** (Multiple Application
  Support; Multiple Instance/window support — the latter enable-on-request).
- **Separate Dashboard.** Management is the **CLM Desktop Dashboard** (its own surface), with the
  same Draft → Ready → Production staging as core.
- **Prerequisites gate everything.** Whitelist Whatfix domains + install the required apps + meet
  **system requirements** (Windows 10 / .NET 4.3; Java 1.7+ only for Java targets; 8 GB RAM). No
  Player installed → no content delivered.
- **Data-center choice on Player install** (US or EU); avoid multiple Player installs (performance).
- **Offline mode** exists for environments without reliable internet (ships, hospitals, air-gapped).
- **Feature parity with Web is broad but not identical** — Flows, Smart Tips, Beacons, Pop-ups, Self
  Help/Explorer, Task List, Segmentation, Translations, Multi-format, Content Aggregation, Integration
  Hub, QuickRead all exist on Desktop, but capabilities and steps differ; never assume a Web-only
  feature (e.g. Cues, Blocker, Launchers, Hub, the New Visibility Rules, Quick Capture, the Player
  Extension, Custom Roles) is present without checking. Surveys exist only embedded in a Pop-up or
  added to Self Help, not as a standalone widget.
- **Embedded analytics:** Desktop ships **both** Guidance Analytics for Desktop **and** Product
  Analytics for Desktop within this workspace (the latter mirrors the standalone PA product — see
  `product-analytics.md`).
- **Not DAP on OS.** Desktop latches onto specific desktop *applications*; DAP on OS (the `hub`
  workspace, `dap-os.md`) is the separate system-level product (Explorer + Communications). Keep the
  two distinct when triaging a PRD.

---

## The desktop apps: Studio & Player

### Whatfix Desktop Studio (authoring app)

**Source:** https://support.whatfix.com/desktop/docs/en/installing-whatfix-desktop-studio

The **Whatfix Desktop Studio** is the installable authoring application (the desktop analog of the Web
Studio extension). Installed **User-Level** (one profile) or **System-Level** (all users). One Studio
authors content across all attached applications. Has install / **update** / uninstall procedures and
a **Preview Mode**. (Installers pre-November-2023 are deprecated.)

- Update / uninstall: https://support.whatfix.com/desktop/docs/en/update-whatfix-studio
- Download location: https://support.whatfix.com/desktop/docs/en/where-can-i-download-the-installation-files-of-the-whatfix-editor-and-player-apps

### Whatfix Desktop Player (end-user runtime)

**Source:** https://support.whatfix.com/desktop/docs/en/install-whatfix-desktop-player

The **Whatfix Desktop Player** is the installable runtime that renders published content on end
users' machines. Installed user- or system-level; **end users choose a data center (US/EU)** at
install. **Auto-updates** (https://support.whatfix.com/desktop/docs/en/autoupdateswhatfixdesktopplayer).
With **Self Hosting**, the Player communicates directly with your own server instead of Whatfix
domains.

---

## Prerequisites & system requirements

**Source:** https://support.whatfix.com/desktop/docs/en/pre-requisites-to-work-with-whatfix-desktop ·
https://support.whatfix.com/desktop/docs/en/recommended-system-requirements

To create and display Desktop content: (1) **whitelist trusted Whatfix domains**, (2) **install the
required apps** (Studio for authors, Player for end users, plus **Microsoft Accessibility
Insights**). Minimum to author: **Windows 10 with .NET
Framework 4.3**, **Java 1.7+** (only for Java target apps), **8 GB RAM**, 1 GB disk, multi-core CPU.

---

## CLM Desktop Dashboard

**Source:** https://support.whatfix.com/desktop/docs/en/overview-of-the-whatfix-desktop-dashboard ·
https://support.whatfix.com/desktop/docs/en/understand-whatfix-desktop-clm

The **CLM Desktop Dashboard** is where Desktop content is created, organized, configured, and
published. Same **Draft → Ready → Production** stages as core (only Production is live to end users).
User roles & permissions per https://support.whatfix.com/desktop/docs/en/whatfixuserroles.

---

## Multi-application delivery behaviors

- **Multiple Application Support** — display content across multiple desktop apps; widgets latch onto
  the app in focus; one Desktop Studio creates content for all.
  https://support.whatfix.com/desktop/docs/en/multipe-application-support
- **Multiple Instance (window) support** (enable-on-request) — widgets latch onto the specific
  **window** of an app in focus (e.g. separate Microsoft Teams windows).
  https://support.whatfix.com/desktop/docs/en/multiple-instancewindow-support-on-desktop
- **Offline mode** — deliver content without constant internet, for disconnected/remote environments.
  https://support.whatfix.com/desktop/docs/en/offline-mode-of-whatfix-desktop
- **Cross application Flows** — a single Flow that runs across multiple desktop applications without
  breaking (e.g. an onboarding tour spanning several apps).
  https://support.whatfix.com/desktop/docs/en/cross-application-flows-1
- **Trigger a desktop Flow using browser URLs** — bridge a browser action to a desktop Flow.
  https://support.whatfix.com/desktop/docs/en/desktop-flows-referenceable

---

## Content types on Desktop (deltas)

The DAP primitives exist on Desktop with the same names as core (see `dap-core.md` for concepts) —
**Flows, Smart Tips, Beacons, Pop-ups** (incl. Visual Editor, AI creation, Carousel), **Static
Content, Multi-format Outputs** (PDF/ODF/Videos/Slideshows/Links), **Translations**, **Icon
Library**, **Content Archival**, and **Advanced Customization** (Access AC / script history). Notable
Desktop specifics: **Spotlight**, **Flow on Standby**, **Action Buttons**, **cross-application** and
**browser-URL-triggered** Flows. **Flow videos** can carry an **AI Voiceover** with a configurable
**Voice Persona** (both Beta, with voiceovers in 80+ languages) and upload automatically to **Brightcove** (GA).
**Surveys** appear only embedded in a Pop-up or added to Self Help (with Survey Diagnostics).
**Not observed on Desktop** (don't assume): Cues, Blocker, Launchers, and the New Visibility Rules
experience — Desktop uses the classic **Visibility and Display Rule Conditions**. Confirm via "Features available in Whatfix Desktop" before documenting.

- Advanced Customization: https://support.whatfix.com/desktop/docs/en/access-advanced-customization

---

## Self Help & Explorer on Desktop

**Source:** https://support.whatfix.com/desktop/docs/en/clone-what-is-self-help ·
https://support.whatfix.com/desktop/docs/en/groups-in-explorer

**Self Help** on Desktop surfaces curated content in a widget; its browsing component is the
**Explorer**, letting end users access Whatfix content. The old Self Help experience was deprecated
after June 2025 in favour of **Improved Self Help**. **QuickRead** (AI-summarized answers) is
available within Self Help on Desktop too
(https://support.whatfix.com/desktop/docs/en/introduction-to-quickread). **Task List**
(https://support.whatfix.com/desktop/docs/en/what-is-a-task-list) and **Segmentation/Tags**
(https://support.whatfix.com/desktop/docs/en/what-is-segmentation-1) work as on core.

> Note: **Explorer also appears in DAP on OS** (`dap-os.md`) as that product's system-level end-user
> surface. Here, Explorer is the desktop product's Self Help browser. Same name, different product —
> scope by the PRD's surface.

---

## Publishing, hosting & deployment

**Source:** https://support.whatfix.com/desktop/docs/en/enhanced-publishing-experience

Content goes live only when pushed to **Production**; **Enhanced Publishing** and **Selective
Publishing** apply as on core. **Self Hosting**
(https://support.whatfix.com/desktop/docs/en/host-content-on-private-server-4) lets the Player fetch
content from **your own private server** (no external Whatfix domain) — for high-privacy/regulated
environments — with multi-format content export. **End-user authentication** can gate delivery.
**Content Aggregation** (https://support.whatfix.com/desktop/docs/en/content-repository-process) and
**Integration Hub** (https://support.whatfix.com/desktop/docs/en/integration-hub-overview) mirror the
core capabilities.

---

## Analytics on Desktop

DAP for Desktop embeds **two** analytics surfaces in this workspace:

- **Guidance Analytics for Whatfix Desktop** — usage/engagement for Desktop content (per-content
  analytics, summary, unique users, CLM-stage data). https://support.whatfix.com/desktop/docs/en/analytics-dashboard
- **Product Analytics for Whatfix Desktop** — the embedded PA product (User Actions, Event Grouping,
  Funnels, Trend Insights, Dashboards, User Journeys, Cohorts). For PA concepts/terminology see
  **`product-analytics.md`**; here it's scoped to desktop apps.

---

## FAQs, Troubleshooting & Best Practices (folded)

> The workspace has **FAQs** (77), **Troubleshooting** (58), and **Best Practices** (13);
> summarized by theme — retrieve the specific article for an answer.

- **FAQs themes** — General; Compliance & Security; CLM Dashboard; Deployment & Content Delivery;
  Analytics; Content Aggregation; QuickRead (15); Whatfix Content (+ Content Archival); Product
  Analytics (Schedule Insight reports); Create Pop-up with AI.
- **Troubleshooting themes** — **Installation** (incl. Whatfix Player), General, Flows, Dashboard
  (largest), Beacons, Widgets, User Roles, Smart Tips, QuickRead, Improved Self Help, and **Whatfix
  Diagnostics** (per content type).
- **Best Practices** — 13 per-feature guides (content, widgets, publishing, etc.).

---

## Glossary (Desktop)

**Source:** https://support.whatfix.com/desktop/docs/en/whatfixglossary

| Term | Meaning | Web analog |
|---|---|---|
| **DAP for Desktop / Whatfix Desktop** | DAP over native desktop applications. | Whatfix Web |
| **Whatfix Desktop Studio** | Installable authoring app (user/system level). | Studio browser extension |
| **Whatfix Desktop Player** | Installable end-user runtime that renders content. | JS Embed / browser extension delivery |
| **CLM Desktop Dashboard** | Management/publishing surface for Desktop content. | Guidance Dashboard |
| **Explorer (Desktop)** | The desktop Self Help browsing component. | Self Help / Explorer (Web) |
| **Multiple Application Support** | One Studio authors across many desktop apps; widget follows focus. | — |
| **Multiple Instance support** | Widgets latch to a specific app window (enable-on-request). | — |
| **Offline mode** | Deliver content without constant internet. | — |
| **Cross application Flow** | A single Flow spanning multiple desktop apps. | Cross-domain Flows |
| **Self Hosting** | Player fetches content from your own private server. | Self-Hosted / On-Premise |
| **Product Analytics for Desktop** | Embedded PA scoped to desktop apps. | Product Analytics (standalone) |
| **DAP on OS** | SEPARATE system-level product (`hub` workspace) — Explorer + Communications. | (distinct product) |
