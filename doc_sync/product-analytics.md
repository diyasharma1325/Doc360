# Whatfix Product Analytics Functional Reference

> Conceptual reference for Whatfix Product Analytics (PA): capabilities, terminology, feature scope,
> and relationships. Use to ground article drafts in accurate PA concepts and naming. Distilled from
> the **published** PA documentation (verified against the Document360 `product-analytics` workspace,
> 2026-09-25). Concepts only — for exact procedure steps, follow the `Source:` link, which is also a
> valid **cross-link** target. Core PA is covered in depth; the **Enterprise** tier (ECC / Enterprise
> Insights) and **Integration Hub** are covered as overviews (the published articles have their detail). FAQs and
> troubleshooting are folded/summarized, not enumerated. Release Notes and Contact Support excluded.

## Table of Contents

- **[Product Analytics Content Map (published IA snapshot)](#product-analytics-content-map-published-ia-snapshot)**
- **[Overview](#overview)** — What is PA, Track→Analyze→Act, Roles, Enable, CLM Stages
- **[Cross-Cutting Rules & Feature Relationships](#cross-cutting-rules--feature-relationships)** — staging, roles, gating, dependencies, when-to-use
- **[Track](#track)** — User Actions, Goals, Verification, Attributes, Autocapture, Event Grouping
- **[Analyze](#analyze)** — Funnel Insights, Trend Insights, Session Analytics, User Journey, Cohorts, User Lists, Dashboards, Session Replay, Demo Mode, Ask Whatfix AI
- **[Act](#act)**
- **[Integration Hub (overview)](#integration-hub-overview)**
- **[Whatfix Enterprise: ECC & Enterprise Insights (overview)](#whatfix-enterprise-ecc--enterprise-insights-overview)**
- **[FAQs & Troubleshooting (folded)](#faqs--troubleshooting-folded)**
- **[Glossary](#glossary)**

---

## Product Analytics Content Map (published IA snapshot)

> A snapshot of the Document360 category structure and published article inventory for the `product-
> analytics` workspace (307 published articles when it was taken). Use it to see where a feature is
> documented and which categories are likely to hold articles a change affects. It is not refreshed
> automatically, so the live workspace may have moved on since; the knowledge index (kb_index.py) is
> the up-to-date source for what is published now.

- **Whatfix Product Analytics Overview** (13) - What is Product Analytics? · Enable Product
  Analytics for your account · Get Analytics Data across CLM Stages · Product Analytics User Roles
  · Understand the deployment support for Product Analytics features · Product Analytics Glossary
  · Deprecated functionality
  - **→ Security and Compliance** (1) - Whatfix Service Level Agreement (SLA)
  - **→ Identify unique users** (3) - How does Whatfix identify users on the application? · How
    does Whatfix identify users across browsers or devices? · How does Whatfix identify multiple
    users using the same device?
  - **→ Configure Analytics Variables** (2) - Create an Analytics Variable · Visualize Analytics
    Variables in Trend Insights
- **Track end-user engagement** (33) - What is Track? · Autocapture URLs
  - **→ Events** (31) - sub: User Action (13) · Attributes (7) · Event grouping (2) · Autocapture
    (9)
- **Analyze end-user behavior** (75) - What is Analyze?
  - **→ Ask Whatfix AI** (3) - Introduction to Ask Whatfix AI · Use Ask Whatfix AI · Ask Whatfix
    AI Best Practices
  - **→ Funnel Insights** (12)
  - **→ Trend Insights** (16) - 13 directly here - sub: Session Analytics (3)
  - **→ User Journey** (6) - What is User Journey? · Create User Journey · Understand the User
    Journey chart · Copy User Journeys · Export User Journey data · Introduction to Ask Whatfix AI
  - **→ Dashboards** (10)
  - **→ Cohorts** (12)
  - **→ User lists (Static Cohorts)** (9)
  - **→ Demo Mode in Whatfix Analytics** (2) - Introduction to the Demo Mode · Access the Demo
    Mode
  - **→ Session Replay** (4) - Understand Session Replay · Access Session Replay · Filter Session
    Replay · Configure Session Replay Settings
- **Act on insights** (1) - What is Act?
- **Integration Hub** (25)
- **Whatfix Enterprise** (38)
  - **→ Enterprise Control Center (ECC)** (5) - What is Enterprise Control Center? · View
    Applications on the ECC dashboard · View users on the ECC dashboard · Add New Users on the ECC
    dashboard · Edit user roles on the ECC dashboard
  - **→ Enterprise Insights (EI)** (33) - Enterprise Insights Glossary - sub: Summary Insights for
    EI (9) · Trend Insights for EI (10) · Dashboards for EI (9) · User Sentiment score (2) · Event
    groups for EI (2)
- **FAQs** (84)
  - **→ Enterprise Insights** (15) - 9 directly here - sub: Schedule Insight reports in Enterprise
    Insights (6)
  - **→ General** (11)
  - **→ Insights** (36) - 30 directly here - sub: Schedule Insight reports (6)
  - **→ Tracking** (22) - sub: User Actions (8) · Autocapture (14)
- **Troubleshooting** (23)
  - **→ Cohorts** (2) - Pop-ups are showing to incorrect Cohort of users · Unable to see the Users
    option in Visibility Rules
  - **→ Funnel Insights** (2) - Funnel Insights do not capture data correctly · Funnel Insights
    for Page View not capturing data
  - **→ Enterprise Insights** (1) - Corrupted User Attribute in Trend Insights for EI
  - **→ Trend Insights** (10)
  - **→ Static Cohorts (User lists)** (2) - Error: Failed to create user list · Error: Invalid
    format - Please ensure the header and columns are the same as the template.
  - **→ User Action** (3) - No events received message for User Actions · User Actions not
    available in Insights or Cohorts · User Actions showing incorrect data
  - **→ General** (1) - Development environment's data appears in Analytics
  - **→ Autocapture** (2) - ScreenSense has not been configured on this page · This element cannot
    be auto-captured
- **Best Practices** (3) - Ask Whatfix AI Best Practices · Insights Best Practices · User Action
  Best Practices
- **Contact Support** (2) - Contact Support · Provide product feedback
- **Release Notes - Product Analytics** (10)

---

## Overview

### What is Product Analytics?

**Source:** https://support.whatfix.com/product-analytics/docs/en/what-is-product-analytics

Whatfix **Product Analytics** is a **no-code** analytics product that helps businesses track and
analyze how users behave inside an application, surfacing usage, friction, and pain points so teams
make data-driven decisions. It is organized around a **Track → Analyze → Act** framework.

### Track, Analyze, Act

- **Track** — collect and organize event/behavior data (no-code).
- **Analyze** — identify trends, patterns, and insights; pinpoint where to improve.
- **Act** — turn insights into action, primarily by delivering in-app guidance through Whatfix DAP.

### Enable Product Analytics

**Source:** https://support.whatfix.com/product-analytics/docs/en/enable-product-analytics-to-capture-engagement-data

Enabled from the Analytics page ("Enable Whatfix Analytics"). Account-level settings include
blocking analytics from specific environments, capturing data across CLM stages, display timezone
(default GMT+5:30), and the **Session activity timeout** (15 / 30 / 60 minutes).

### Get Analytics Data across CLM Stages

**Source:** https://support.whatfix.com/product-analytics/docs/en/get-analytics-data-across-clm-stages

By default PA shows **Production**-stage data; you can add the **Ready** stage. Engagement is tracked
against the content's stage at the moment of interaction, so the time range and stage must match the
interaction. Stage filtering applies across Trends, Funnels, User Journeys, Dashboards, Cohorts, and
Guidance Analytics; moved/deleted content is badged.

### Product Analytics User Roles

**Source:** https://support.whatfix.com/product-analytics/docs/en/product-analytics-user-roles

The first user in an enterprise becomes the **Account Manager**. Only **Account Manager** and
**Content Manager** roles can access the Analytics dashboard; **Editor** and **Translator** cannot.
Adding a user to Analytics also adds them to the Guidance dashboard with the same role.

---

## Cross-Cutting Rules & Feature Relationships

> Constraints, dependencies, and decisions that span PA features — the relational nuance that makes
> guidance accurate.

### Staging & data scope

- Analytics default to **Production**; **Ready** can be added. Data is attributed to the content's
  stage at interaction time.
- **Session data** is captured only for accounts that pushed to Production **after May 20, 2025**.
- **Data availability is a fixed policy, not a setting:** Whatfix stores analytics data for up to
  **two years**; **Insights** show up to one year; **Dashboards** reach back one year but show only
  **six months** at a time; **Self Help shown** and **Smart-tip loaded for page** events are kept
  for only **three months**. Older data or deletion requests go through support. Data is retained
  for two years after contract termination (`how-long-does-whatfix-product-analytics-retain-data`).
  The display **timezone** (default GMT+5:30) is account-configurable.

### Roles

- Only **Account Manager** and **Content Manager** use the Analytics dashboard; Editor/Translator
  are excluded. First enterprise user = Account Manager.

### Deployment & feature gating

- **Deployment support varies by feature** — see "Understand the deployment support for Product
  Analytics features" (`understand-the-deployment-support-for-product-analytics-features`).
  Notably, **Integration Hub is NOT available on Self-Hosted**, **Session Replay is Cloud-only**,
  and **AI Summaries / Ask Whatfix AI** use cloud-hosted models even on-premise.
- **Beta / enable-via-support features** (don't assume on): **Autocapture**, **Event Attributes**,
  **User Attributes**, **Session Replay**, **Cohorts as Visibility Rules**, **Real Time Cohorts**,
  **User Lists in Visibility Rules**, **Enterprise Insights**, **Enterprise Control Center (ECC)**
  (selected customers only), **New Guidance Analytics Dashboard**, **Metrics in Trend Insights**,
  and **Track Process Funnels** (Beta, premium). **Ask Whatfix AI** (and AI Summaries) is part of
  the **PA AI add-on** (Insights Agent), enabled via your CSM.

### Key dependencies & relationships

- **PA works with OR without DAP** (FAQ: "Can I use Product Analytics without DAP?" — yes). Its
  **Act** stage is where PA feeds back into DAP (a friction insight → a new Smart Tip/Flow).
- **Unique-user metrics require User Identification**; otherwise users are anonymized Whatfix IDs.
  The **Event identification rate** shows the share of events attributable to identified users.
- **Autocapture depends on Smart Context** and on elements having strong HTML identifiers (ID/class);
  it captures **click events only** (not hover/text), and Event Attributes can't be captured from an
  Autocaptured event directly (convert it to a User Action first, then capture them).
- **Sessions** end on tab close/switch, new tab, or inactivity past the timeout; each is a unique
  session ID.
- **Cross-product note:** **Whatfix Mirror does NOT support User Journeys** (Trends and Funnels work
  there). Mirror also has its own embedded "Product Analytics for Mirror" — distinct from this
  standalone PA workspace.

### When to use which

- **User Action vs Autocapture** — a manually defined critical event (precise, supports Event
  Attributes, hover/text triggers) vs automatic click capture with retroactive data (fast, broad).
- **Cohort vs User List (Static Cohort)** — a rule-based, dynamic group vs a fixed list uploaded by
  CSV of User IDs.
- **Trend Insights vs Funnel Insights** — aggregate engagement/trends of events over time vs
  drop-off across a sequential step path. (**Funnels vs User Journey** — a predefined sequence vs
  open exploration of all paths users actually take.)
- **Insights vs Session Replay** — *what* users did (quantitative) vs *why* (qualitative, video-like
  replay of an individual session).

---

## Track

### What is Track?

**Source:** https://support.whatfix.com/product-analytics/docs/en/track

Track captures user actions and behaviors on a website/application with no-code, user-friendly event
capture. A visual drag-and-drop tagging editor sets up tracking for clicks, page visits, scrolls,
and more without technical expertise.

### User Actions

**Source:** https://support.whatfix.com/product-analytics/docs/en/user-action

A **User Action** tracks an end-user interaction/behavior, even when the user doesn't engage with
Whatfix content. **Not visible to end users** (unlike Flows/Smart Tips/Beacons). Drives data-driven
decisions across product, CS, marketing, and support; usable as **Visibility Rules** and as **Funnel
/ Journey** events. Related:
- **Goals** — a User Action created on the *final* element of a process (e.g. **Save**) so a task
  counts complete even if the guiding Flow was abandoned early.
- **User Action Verification** — verify a User Action is firing correctly; has defined statuses.
- **User Action Completion Rules** — define when a User Action is considered complete (e.g. Page
  View completion).

### Attributes (Event & User) and Analytics Variables

**Event Attributes** (Beta) are contextual values captured alongside an event (e.g. the competitor
name entered when a User Action on **Save** fires, or a dropdown selection); add them to Trend
Insights for richer breakdowns. **User Attributes** (Beta) are user properties (ID, email,
department, business unit, location) captured via Advanced Customization, used to filter and break
down Insights; user information must be set with `wfx_settings` first. (Event Attributes can't be
captured from Autocaptured events directly; convert the event to a User Action first.)

**Analytics Variables** (GA 2026; `create-an-analytics-variable`) capture values from the end
user's application (Local Storage, cookies or Window Variables) without writing code, up to **10**
per account, created under Settings → Advanced customisation → User rules. Each is either a
**Context Variable** (tracked with every captured Whatfix event; e.g. an Invoice ID) or a **User
Attribute** (tracked when its value changes; e.g. role or region), and both can filter and break
down Insights. A Context Variable also serves as the **Process key** for Track Process Funnels.

### Autocapture (Beta)

**Source:** https://support.whatfix.com/product-analytics/docs/en/what-is-autocapture

**Autocapture** automatically records **click events** across the app without manual User-Action
setup, surfacing the most-engaged events to save and analyze (Undefined → Defined events). Gives
**retroactive** data (no waiting to instrument). **Requires Smart Context**; only tracks elements
with strong HTML identifiers; **click events only** (hover/text need User Actions); **no Event
Attributes** from Autocaptured events directly (convert to a User Action first). Visualizable in
Trends, Funnels, and User Journeys. Separately, **Autocapture URLs** captures page and URL data
(page views, session count, URL metadata) automatically with no configuration and no PII.

### Event grouping

Group two or more Default/Custom events into a single grouped event to analyze combined metrics,
then visualize the group in Trend Insights.

---

## Analyze

**Source:** https://support.whatfix.com/product-analytics/docs/en/analyze

Explore how users behave through Funnels, Trends, User Journeys, Cohorts, Dashboards, Session
Analytics, and Session Replay.

### Funnel Insights

**Source:** https://support.whatfix.com/product-analytics/docs/en/what-are-funnels

A **Funnel** is a sequence of events showing how users progress through a process — completion
rates, highest-drop-off steps, and time between steps. Steps can be Flows, User Actions, Autocaptured
events, or Page Views (the events must exist first). **Conversion Funnels** track discovery-to-
conversion paths
(`what-can-i-do-with-conversion-funnels`). Funnels can be analyzed by **Unique users** (first
attempt only) or **Total attempts** (every attempt), and can be compared, downloaded, and copied.
**Track Process Funnels** (Beta, premium) group events by a shared **Process key** (e.g. an
Opportunity ID) so one business process can be followed across several users and sessions, with
Completion Rate, Total Processes Started and Completion Time.

### Trend Insights

**Source:** https://support.whatfix.com/product-analytics/docs/en/trend-insights-1

**Trend Insights** turn engagement questions into visual charts (e.g. users who completed a Flow).
Built from Metrics (Total events, Unique users + Session metrics), Events (Guidance vs App), Event
Filters/Breakdowns, and User Filters/Breakdowns (browser, OS, city, country, User ID, attributes).
Up to **10 events** per insight. Multiple chart types; schedulable as reports.

### Session Analytics

**Source:** https://support.whatfix.com/product-analytics/docs/en/understand-session-analytics

Session metrics (Total sessions, Average/Total session time, Avg sessions per user, Avg time per
user) reveal engagement frequency/duration — e.g. frequent short sessions signal friction. A
**session** is actions in one browser tab within a time window, ending on tab close/switch or
inactivity past the timeout. (Session data only for accounts that pushed to Production after
2025-05-20.)

### User Journey

**Source:** https://support.whatfix.com/product-analytics/docs/en/user-journey

**User Journey** visualizes the actual paths users take (Sankey chart) using User Actions,
Autocaptured events, or API events — surfacing common paths, high/low engagement, and drop-off.
**Not supported in Whatfix Mirror.**

### Cohorts & User Lists

**Sources:** https://support.whatfix.com/product-analytics/docs/en/what-is-a-cohort ·
https://support.whatfix.com/product-analytics/docs/en/what-are-static-cohorts-user-lists

A **Cohort** groups users by criteria/behavior (dynamic, rule-based); usable in Insights, as
Visibility Rules (Beta), or exported. A **User List (Static Cohort)** is a fixed group built by
uploading a CSV of User IDs (IDs must match Whatfix's unique identifier) — for targeting or
including/excluding users (e.g. internal testers, A/B groups). A Cohort can be derived from a User
List.

### Dashboards

**Custom Dashboards** assemble Insights (Trends, Funnels, etc.) into a single view with tabs, for
at-a-glance, data-driven decisions; create, customize, tab, export, copy, edit, share.

### Session Replay (Beta)

**Source:** https://support.whatfix.com/product-analytics/docs/en/understand-session-replay

A visual tool that reconstructs an end user's session as a **video-like** playback (DOM-mutation
tracking) — clicks, scrolls, navigations, and engagement with Whatfix content / User Actions /
Defined Autocaptured events — adding the *why* behind Insights (investigate drop-offs, low NPS,
friction). **Cloud-only Beta** (JS Embed + Extension); relies on Session/Local Storage (**not**
incognito); **auto-masks PII**; works with the event-capture framework (it doesn't capture events
itself).

### Demo Mode

Demo Mode presents sample/illustrative analytics data — useful for exploring the product or demos
without real data (`introduction-to-demo-mode`).

### Ask Whatfix AI

**Source:** https://support.whatfix.com/product-analytics/docs/en/introduction-to-ask-whatfix-ai

The **Insights Agent** of the **PA AI add-on** (enabled via your CSM): it converts a natural-language
engagement question into a Trend Insight, Funnel Insight or User Journey, and powers the
**Summarize** action (AI Summary) on Insights. Deep reasoning is built in (the separate Deep think
toggle is gone), its thinking can be shown or hidden, and it can also answer product and
metric-definition questions from the Whatfix support knowledge base. It asks clarifying questions
when a query is ambiguous, suggests follow-up questions, keeps **chat history for one year**, and
accepts `@` mentions of specific events. No PII (such as user IDs) is sent to the model.

---

## Act

**Source:** https://support.whatfix.com/product-analytics/docs/en/act

**Act** translates insights into action without waiting on engineering: primarily **creating in-app
experiences through Whatfix DAP** (e.g. a Smart Tip or Flow at a high-friction step), plus
data-driven product decisions (prioritize features, remove friction).

---

## Integration Hub (overview)

**Source:** https://support.whatfix.com/product-analytics/docs/en/integration-hub-overview-1

Part of Whatfix's **Open Ecosystem Platform** — exchange data and attribute streams with other
products via **APIs and Webhooks** (uni- or bi-directional) to unify insights, segment content, and
automate tasks/notifications. ~20 prebuilt integrations (Amplitude, Confluence, FullStory, Google
Analytics, Google Sheets, Bullhorn, …) plus **Enterprise Attributes** for segmentation. Backend
setup is done by Whatfix (contact support). **Not available on Self-Hosted.** (Per-integration
detail lives in the published articles.)

---

## Whatfix Enterprise: ECC & Enterprise Insights (overview)

> The enterprise tier for organizations running Whatfix across **multiple applications/accounts
> (ENTs)**. Covered here as overviews; per-feature detail is in the published articles.

### Enterprise Control Center (ECC) (Beta)

**Source:** https://support.whatfix.com/product-analytics/docs/en/enterprise-control-center

Centralized management of Whatfix across multiple applications: view all org accounts, open a
specific ENT, manage users/roles across apps at once, view cross-application insights, build
dashboards, and analyze license utilization, adoption, and user sentiment. Beta (selected
customers).

### Enterprise Insights (EI)

Org-level, cross-application analytics: **Summary Insights for EI** (metrics, filters, metric
comparison, **Application Utilisation** and **Adoption score**), **Trend Insights for EI** (+ EI
Session Analytics), **Dashboards for EI**, **User Sentiment score**, and **Event groups for EI**.
Reports are schedulable. Use EI to compare application performance across the org and find the apps
with the lowest reception.

---

## FAQs & Troubleshooting (folded)

The PA workspace has large FAQ (~84) and Troubleshooting (~23) categories; their facts belong with
the relevant feature above. High-value ones to know:

- **Can I use PA without DAP?** Yes. **Do end users need a Whatfix account?** No.
- **Unique-user discrepancies** (Guidance Analytics vs Funnel) stem from identification/timing —
  ensure User Identification is configured.
- **Excluding test User IDs / blank values / unidentified users** is supported in Insights filters.
- **Autocapture:** works on single-page apps; converting an Autocaptured event to a User Action;
  why an element "cannot be auto-captured" (no strong identifier / Smart Context — "ScreenSense not
  configured").
- **Trend Insights limits:** max 10 events per insight; "Create insights button grayed out" and
  "no events received" troubleshooting.
- **Static Cohort upload errors:** CSV header/columns must match the template.

---

## Glossary

| Term | Meaning |
|---|---|
| **Product Analytics (PA)** | No-code product for tracking/analyzing user behavior. |
| **Track / Analyze / Act** | The three-stage PA framework. |
| **User Action** | A tracked end-user interaction; not visible to end users. |
| **Goal** | A User Action on the final element marking a process complete. |
| **Autocapture** | Auto-captured click events (Beta; needs Smart Context). |
| **Event / User Attribute** | Properties on an event / on a user, used for breakdowns & segmentation. |
| **Funnel Insight** | Sequential-event drop-off/completion analysis. |
| **Trend Insight** | Visual trends of event/session metrics over time. |
| **Session Analytics** | Session frequency/duration metrics. |
| **User Journey** | Sankey visualization of paths users take (not in Mirror). |
| **Cohort** | Dynamic rule-based user group. |
| **User List (Static Cohort)** | Fixed user group from an uploaded CSV. |
| **Dashboard** | A composed view of multiple Insights. |
| **Session Replay** | Video-like reconstruction of a session (Beta, Cloud-only). |
| **Ask Whatfix AI** | Insights Agent (PA AI add-on) that turns questions into Insights and summarizes them. |
| **Analytics Variable** | A captured app value, as a Context Variable or a User Attribute (up to 10). |
| **Track Process Funnel** | A Funnel grouped by a Process key across users and sessions (Beta, premium). |
| **ECC** | Enterprise Control Center — manage Whatfix across multiple apps. |
| **Enterprise Insights (EI)** | Org-level, cross-application analytics (utilization, adoption, sentiment). |
