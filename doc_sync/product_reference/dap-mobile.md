# Whatfix DAP for Mobile — Surface Delta Reference

> Mobile-specific model for the Whatfix Digital Adoption Platform: how content is authored,
> structured, targeted, deployed, and measured **on native mobile apps**. This is a DELTA on top of
> `dap-core.md` for the shared DAP philosophy (in-app, no-code, contextual guidance; CLM staging;
> roles). **Mobile has its OWN content taxonomy** — it does NOT reuse the Web primitives. Where a
> Web concept has a different Mobile name, that is called out (e.g. Web **Flow** → Mobile
> **Walkthrough**; Web **Studio browser extension** → Mobile **Creator Widget + SDK**; Web
> **Segmentation** → Mobile **User Segments / User Properties**). Do not assume a Web feature exists
> on Mobile, or vice versa.
>
> Distilled from the **published** Whatfix Mobile documentation, **verified against the live
> Document360 `mobile` workspace on 2026-09-25** (Release Notes and Contact
> Support excluded). Concepts only — for exact steps, follow the `Source:` link (canonical
> `/mobile/docs/en/` form), which is also a valid **cross-link** target. Archived/deprecated/
> unpublished docs are excluded.

## Table of Contents

- [Mobile Content Map (published IA snapshot)](#mobile-content-map-published-ia-snapshot)
- [What Whatfix Mobile is](#what-whatfix-mobile-is)
- [Cross-Cutting Rules & Mobile Relationships](#cross-cutting-rules--mobile-relationships)
- [SDK integration (the deployment model)](#sdk-integration-the-deployment-model)
- [Authoring model: Creator Widget, Apps, Projects](#authoring-model-creator-widget-apps-projects)
- [Mobile content taxonomy](#mobile-content-taxonomy)
- [Targeting: User Segments & User Properties](#targeting-user-segments--user-properties)
- [Callbacks & Events](#callbacks--events)
- [Publishing & hosting](#publishing--hosting)
- [Whatfix for Mobile Web](#whatfix-for-mobile-web)
- [Insights (analytics) & Debugging](#insights-analytics--debugging)
- [Language & localization](#language--localization)
- [FAQs & Best Practices (folded)](#faqs--best-practices-folded)
- [Glossary (Mobile)](#glossary-mobile)

---

## Mobile Content Map (published IA snapshot)

> A snapshot of the Document360 category structure and published article inventory for the `mobile`
> workspace (200 published articles when it was taken). Use it to see where a feature is documented
> and which categories are likely to hold articles a change affects. It is not refreshed
> automatically, so the live workspace may have moved on since; the knowledge index (kb_index.py) is
> the up-to-date source for what is published now.

- **Whatfix Mobile Overview** (9)
- **Install Whatfix Mobile** (32) - Latest Whatfix Mobile SDKs Changelog
  - **→ Android** (6)
  - **→ iOS** (3) - Integrate Whatfix Mobile SDK with iOS · iOS Changelog · Tag iOS Views
  - **→ React Native** (4) - Integrate Whatfix Mobile SDK with React Native Android · Integrate
    Whatfix Mobile SDK with React Native iOS · Tag React Native Views in Android and iOS · React
    Native Changelog
  - **→ Xamarin** (4) - Integrate Whatfix Mobile SDK with Xamarin Android · Integrate Whatfix
    Mobile SDK with Xamarin iOS · Xamarin Android Changelog · Xamarin iOS Changelog
  - **→ Cordova** (4) - Integrate Whatfix Mobile SDK with Cordova Android · Integrate Whatfix
    Mobile SDK with Cordova iOS · Cordova Android Changelog · Cordova iOS Changelog
  - **→ Ionic** (2) - Integrate Whatfix Mobile SDK with Ionic(Android/iOS) · Ionic Changelog
  - **→ Jetpack Compose** (2) - Integrate Whatfix Mobile SDK with Jetpack Compose · Jetpack
    Compose Changelog
  - **→ MAUI** (4) - Integrate Whatfix Mobile SDK with MAUI (Android) · Integrate Whatfix Mobile
    SDK with MAUI (iOS) · MAUI Android Changelog · MAUI iOS Changelog
  - **→ Flutter** (2) - Integrate Whatfix Mobile SDK with Flutter · Flutter Changelog
- **Whatfix Administration** (6) - 5 directly here
  - **→ Security and Compliance** (1) - Whatfix Service Level Agreement (SLA)
- **Create Whatfix Content** (83) - How does Whatfix Mobile work?
  - **→ In-app experience** (14)
  - **→ Walkthrough** (13) - 9 directly here - sub: Configure Walkthrough Menu (2) · Configure
    Walkthrough Checklist (2)
  - **→ Standalone Projects** (25) - Save Project Designs as Templates · Customize Button Actions
    for Standalone Projects - sub: Tooltip (3) · Bottom Sheet (3) · Gestures (2) · Full Screen (3)
    · Drawer (3) · Beacons (3) · Highlights (3) · Pop-Ups (3)
  - **→ Survey** (5)
  - **→ Carousel** (3) - What is a Carousel? · Create a Carousel · Customize Carousels
  - **→ Delight** (5)
  - **→ Language Support** (5)
  - **→ Publish Whatfix Content** (12) - 6 directly here - sub: Use Cases for publishing using
    Project ID (3) · Self Hosting (3)
- **Organize Whatfix Content** (6)
  - **→ User Segments** (6)
- **Integration Hub** (1) - Mixpanel Cohort Integration
- **Whatfix Mobile Callbacks and Events** (6)
- **Guidance Analytics** (4) - Insights Overview · Whatfix Mobile Locale codes · User Level
  Insights for Checklist · Identify unique users in Whatfix Mobile
- **Whatfix for Mobile Web** (1) - Create content using Whatfix for Mobile Web
- **Debugging Tools for Whatfix Mobile** (3) - Access Debugging tools in Whatfix Mobile ·
  Understand Setup data in Self Debugging panel · Share Technical Logs for Debugging
- **FAQs** (32)
  - **→ General** (13)
  - **→ Deployment and Content Delivery** (11)
  - **→ Whatfix Mobile Content** (7)
  - **→ Performance and Security** (1) - How secure is Whatfix?
- **Release Notes** (12)
- **Contact Support** (1) - Contact Support
- **Best Practices** (4) - In-app Messages Best Practices · Operating Systems, Device
  Compatibility, and Performance Impact · Nudges Best Practices · Walkthrough Best Practices

---

## What Whatfix Mobile is

**Source:** https://support.whatfix.com/mobile/docs/en/what-is-whatfix-mobile

**Whatfix Mobile** is the DAP built specifically for **native mobile apps** — onboarding, training,
and engaging mobile users with contextual, **no-code** in-app experiences. The delivery solution
depends on source-code access:

- **Whatfix Mobile SDK** — when you have the app's source code (the primary, full-capability path).
- **Whatfix for Mobile Web** — for web apps surfaced on mobile (see that section).

**Source:** https://support.whatfix.com/mobile/docs/en/what-can-you-do-with-whatfix-mobile ·
https://support.whatfix.com/mobile/docs/en/features-available-in-whatfix-mobile

---

## Cross-Cutting Rules & Mobile Relationships

> The relational nuance specific to Mobile. Confirm before asserting a default; several features are
> enable-on-request.

- **Mobile is a distinct product from Web DAP.** Native content (Walkthroughs, Standalone Projects)
  is authored and delivered via the **SDK + Creator Widget + Mobile Dashboard**, NOT Whatfix Studio.
  Web content types (Flows, Smart Tips, Self Help, Cues, Visibility Rules) do **not** apply to native
  Mobile. The one bridge is **Whatfix for Mobile Web**, which reuses the Web Studio flow.
- **SDK is the dependency for everything.** No SDK integration → no native in-app experiences. The
  **Creator SDK** is development/testing only and **must be excluded from production builds**; the
  runtime SDK ships in production.
- **App + App Version scoping.** Content is created against an **App** and a specific **App Version**;
  switching versions affects which content applies (content can be copied across versions).
- **Content updates need no app-store release.** Publishing/unpublishing is server-side and takes
  effect without an app update (unless Self Hosting, where you control distribution).
- **Cross-platform authoring.** A Walkthrough authored on one OS can apply to the other (see FAQs:
  "Can a Flow created on iOS work on Android?") — element identification is by reference.
- **Enable-on-request / config-dependent:** **Self Hosting** (also needs a minimum SDK version),
  **Mobile Web** (needs a Web DAP subscription), and some framework/OS combinations — confirm
  availability via Feature Availability or support. **Offline Support** is on by default for
  directly published Projects (users must go online once to download them); Projects published by
  Project ID need an explicit `offlineSync` call at app start.
- **Targeting differs from Web:** use **User Segments** built from **User Properties** (default +
  custom), not Web Segmentation/Tags/Visibility Rules.

---

## SDK integration (the deployment model)

**Source:** https://support.whatfix.com/mobile/docs/en/what-is-whatfix-mobile-sdk

The **Whatfix Mobile SDK** is integrated into the app per framework. Supported frameworks:
**Android** (incl. **Jetpack Compose**, **WebView**), **iOS**, **React Native** (Android & iOS),
**Xamarin** (Android & iOS), **Cordova** (Android & iOS), **Ionic**, **MAUI** (Android & iOS), and
**Flutter**. Each has its own integration article and changelog; common Android tasks include
creating an Application Class, tagging views, and Audio Ducking.

- Android: https://support.whatfix.com/mobile/docs/en/integrate-whatfix-mobile-sdk-with-android
- iOS: https://support.whatfix.com/mobile/docs/en/integrate-whatfix-mobile-sdk-with-ios
- WebView support: https://support.whatfix.com/mobile/docs/en/webview-support
- Trusted domains to whitelist: https://support.whatfix.com/mobile/docs/en/what-are-the-trusted-whatfix-mobile-domains-to-whitelist

---

## Authoring model: Creator Widget, Apps, Projects

### Whatfix Creator Widget

**Source:** https://support.whatfix.com/mobile/docs/en/whatfix-creator-widget

The **Whatfix Creator Widget** is the in-app authoring interface (the Mobile analog of the Web
Studio extension). It appears after the **Creator SDK** is integrated and is used **only during
development/testing** — view app details, **stream and capture app screens**, identify/target
elements, and preview. The production app must **exclude** the Creator SDK.

### Apps, Projects & App Versions

**Source:** https://support.whatfix.com/mobile/docs/en/what-is-an-in-app-experience-or-project ·
https://support.whatfix.com/mobile/docs/en/how-does-whatfix-mobile-work

Mobile content is organized as **Projects** (an "in-app experience"), made of a **Project type**
(e.g. Onboarding & Training, Nudges) and **Elements** (Walkthroughs, Tooltips, Beacons, etc.). You
**add an App** to the Dashboard, **create a Project**, capture screens, build the experience, and
preview on a **device or emulator** (QR/secret to connect). Content is scoped to an **App Version**.

- Add an App / Create a Project: https://support.whatfix.com/mobile/docs/en/create-a-project · https://support.whatfix.com/mobile/docs/en/create-a-project-1
- Stream & capture screens: https://support.whatfix.com/mobile/docs/en/stream-and-capture-app-screens
- App Version: https://support.whatfix.com/mobile/docs/en/app-version
- Preview on a device: https://support.whatfix.com/mobile/docs/en/preview-projects-on-a-device

---

## Mobile content taxonomy

> Mobile elements are NOT the Web primitives. Map carefully.

### Walkthrough (≈ Web Flow)

**Source:** https://support.whatfix.com/mobile/docs/en/what-are-flows

A **Walkthrough** is a series of steps layered over the app to teach an objective or complete a task
— the Mobile equivalent of a Web **Flow**. Each step is a Mobile **element** (Pop-up, Bottom Sheet,
Tooltip, Full Screen, Highlight, Gesture). Related: **Walkthrough Menu** (a launchable menu of
walkthroughs) and **Walkthrough Checklist** (a task-checklist, with optional sub-flow auto-start).

- Walkthrough Menu: https://support.whatfix.com/mobile/docs/en/what-is-walkthrough-menu
- Walkthrough Checklist: https://support.whatfix.com/mobile/docs/en/what-is-a-walkthrough-checklist

### Standalone Projects (single-element experiences)

A **Standalone Project** is a single element shown on its own (not part of a Walkthrough). Types:

- **Tooltip** — contextual callout on an element. https://support.whatfix.com/mobile/docs/en/what-is-a-tooltip
- **Bottom Sheet** — panel sliding up from the bottom. https://support.whatfix.com/mobile/docs/en/what-is-a-bottom-sheet
- **Gesture** — guided swipe/tap gesture cue. https://support.whatfix.com/mobile/docs/en/what-is-a-gesture
- **Full Screen** — full-screen takeover message. https://support.whatfix.com/mobile/docs/en/what-is-a-full-screen
- **Drawer** — side panel for announcements/promotions without covering the screen. https://support.whatfix.com/mobile/docs/en/introduction-to-drawer
- **Beacon** — attention marker on an element. https://support.whatfix.com/mobile/docs/en/introduction-to-beacons
- **Highlight** — emphasis on an element/region. https://support.whatfix.com/mobile/docs/en/what-is-a-highlight
- **Pop-Up** — modal informational widget. https://support.whatfix.com/mobile/docs/en/what-is-a-pop-up

Designs can be **saved as Templates** (https://support.whatfix.com/mobile/docs/en/save-designs-as-templates).

### Survey, Carousel, Delight

- **Survey** — in-app feedback from two built-in templates (**Feedback** and **NPS**), with question types and **Survey Insights**. https://support.whatfix.com/mobile/docs/en/introduction-to-surveys
- **Carousel** — a swipeable multi-card experience. https://support.whatfix.com/mobile/docs/en/what-is-a-carousel
- **Delight** — celebratory effects on task completion: **Snowfall, Confetti, Fireworks, Audio**. https://support.whatfix.com/mobile/docs/en/introduction-to-delight

---

## Targeting: User Segments & User Properties

**Source:** https://support.whatfix.com/mobile/docs/en/user-segment ·
https://support.whatfix.com/mobile/docs/en/what-is-a-user-property

Mobile targeting uses **User Segments** — reusable groups of users defined by **User Properties**,
auto-updating as users interact (e.g. "installed the app 30 days ago"). Both come in **Predefined/
Default** (captured by the SDK with no config) and **Custom** variants. **Custom Properties** extend
targeting; **Personalization** tailors the in-app experience per user.

- Custom Properties: https://support.whatfix.com/mobile/docs/en/add-custom-properties-to-user-segments
- Personalization: https://support.whatfix.com/mobile/docs/en/personalization

---

## Callbacks & Events

**Source:** https://support.whatfix.com/mobile/docs/en/whatfix-mobile-events ·
https://support.whatfix.com/mobile/docs/en/setup-whatfix-mobile-callbacks

Whatfix Mobile generates **Events** when users interact with a Walkthrough or element (the basis of
Insights), modeled on two entities: **Element** (a single interaction on one screen) and **Flow**
(multiple interactions across screens). Events can be sent to third-party platforms via integrations
or custom code. **Callbacks** let the host app react to Whatfix activity. Event families:
**Events for Elements**, **Events for Flow Menu**, **Events for Static Flow**.

---

## Publishing & hosting

**Source:** https://support.whatfix.com/mobile/docs/en/publish-whatfix-content

A Project is published to go live with **no app update**, two ways:

- **Publish directly** — target a **User Segment** from the Dashboard; shown to all users in that segment.
- **Publish using Project ID** — a unique ID initialized in code (`startProject(projectID)`), useful
  to target segments from a third-party analytics platform / your own data warehouse. Use cases:
  auto-start a sub-flow in a checklist, launch on button click, launch via notification.
  https://support.whatfix.com/mobile/docs/en/publish-using-project-id

Related: **Assign Project Priority**
(https://support.whatfix.com/mobile/docs/en/assign-project-priority) and **Offline Support**
(https://support.whatfix.com/mobile/docs/en/whatfix-mobile-offline-support): automatic for direct
publishing once the user has been online, and an explicit `offlineSync` of the Project IDs at app
start for Project-ID publishing.

### Self Hosting

**Source:** https://support.whatfix.com/mobile/docs/en/self-hosting-whatfix-mobile-content

**Self Hosting** (enable via support) exports the in-app experience as a `.zip` to host on your CDN/
private server — for internal networks or IT policies that block loading from the Whatfix cloud. Has
its own **App Versioning** and documented **limitations**.

---

## Whatfix for Mobile Web

**Source:** https://support.whatfix.com/mobile/docs/en/create-content-using-whatfix-for-mobile-web

**Mobile Web** surfaces **web applications** as mobile guidance — creation mirrors the Web DAP flow
(requires the **Web DAP** subscription and the **Whatfix Studio** browser extension on Chrome/Edge),
not the native SDK path. Use this when the "mobile" target is a web app rather than a native app.

---

## Insights (analytics) & Debugging

**Source:** https://support.whatfix.com/mobile/docs/en/analytics-dashboard

**Whatfix Mobile Insights** reports usage/engagement for Mobile content — app performance, user
engagement, completion rate, project views; most data refreshes daily at 00:00 GMT (User-Level
Insights differ). Related: **unique-user identification**
(https://support.whatfix.com/mobile/docs/en/identify-unique-users-in-whatfix-mobile-insights),
checklist user-level insights, and locale codes.

**Debugging Tools** — a **Self Debugging panel** (access, setup data) and the ability to **share
technical logs** for support. https://support.whatfix.com/mobile/docs/en/access-self-debugging-panel-in-whatfix-mobile

**Integration Hub (Mobile)** currently documents **Mixpanel Cohort Integration**
(https://support.whatfix.com/mobile/docs/en/mixpanel-cohort-integration).

---

## Language & localization

**Source:** https://support.whatfix.com/mobile/docs/en/set-app-locale

Mobile supports per-project localization: **Set App Locale**, add languages, add translated text,
and add/generate **Audio** (including multilingual audio) for in-app experiences. Target experiences
by the user's device language (see FAQs).

---

## FAQs & Best Practices (folded)

> The workspace has **FAQs** (32) and **Best Practices** (4); summarized here, retrieve the specific
> article for an answer.

- **FAQs themes** — General (frameworks/OS supported, hybrid apps, SDK permissions, API token, deep/
  external links, image size limits, supported languages, Dashboard browser); Deployment & Content
  Delivery (direct vs Project-ID publishing, SDK update cadence, where content is stored, invalid
  Project ID behavior, device-language targeting, Backbase support); Whatfix Mobile Content
  (cross-OS content, custom fonts, element targeting/identification by reference, project sequencing,
  copying content across app versions, missing page identifiers); Performance & Security.
- **Best Practices** — In-app Messages, Walkthroughs, Nudges, and Operating-Systems/Device-
  Compatibility/Performance impact.

---

## Glossary (Mobile)

**Source:** https://support.whatfix.com/mobile/docs/en/whatfixglossary

| Term | Meaning | Web analog |
|---|---|---|
| **Whatfix Mobile SDK** | Native library integrated into the app to deliver in-app experiences. | (Studio extension / JS Embed) |
| **Creator SDK / Creator Widget** | Dev/test-only authoring interface; excluded from production. | Whatfix Studio |
| **App / App Version** | The mobile app and a specific version content is scoped to. | — |
| **Project / In-app experience** | A unit of authored content (Project type + Elements). | (a piece of content) |
| **Walkthrough** | Multi-step guided experience over the app. | Flow |
| **Walkthrough Menu / Checklist** | Launchable menu / task checklist of walkthroughs. | Self Help / Task List |
| **Standalone Project** | A single-element experience (Tooltip, Beacon, etc.). | — |
| **Tooltip / Beacon / Pop-Up / Highlight** | Element types shown on an app screen. | Smart Tip / Beacon / Pop-up |
| **Bottom Sheet / Drawer / Full Screen / Gesture** | Mobile-only element types. | — |
| **Carousel** | Swipeable multi-card experience. | — |
| **Delight** | Celebratory effect (Snowfall/Confetti/Fireworks/Audio). | — |
| **User Segment / User Property** | Reusable user group / the rules defining it. | Segmentation / Attributes |
| **Project ID publishing** | Publish + initialize a project in code via a unique ID. | — |
| **Self Hosting** | Export content as a `.zip` to host on your own CDN/server. | Self-Hosted/On-Premise |
| **Mobile Web** | Web apps surfaced as mobile guidance (uses Web Studio). | Web DAP |
| **Insights** | Mobile usage/engagement analytics. | Guidance Analytics |
| **Callbacks / Events** | Host-app hooks / interaction events for Insights & integrations. | (Callbacks/Events) |
