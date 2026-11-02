# Whatfix DAP for Web — Surface Delta Reference

> Web-specific mechanics for the Whatfix Digital Adoption Platform: how content is authored,
> deployed, hosted, and constrained **on the web surface**. This is a DELTA on top of `dap-core.md`
> — the shared concepts (Flows, Smart Tips, Beacons, Pop-ups, Launchers, Cues, Surveys, Task List,
> Self Help, Hub, Segmentation, Tags, Visibility Rules, ScreenSense, AI Agents, etc.) are NOT
> repeated here; read `dap-core.md` for those. Web is the primary DAP surface.
>
> Distilled from **published** documentation, **verified against the live `studio` (DAP Web)
> workspace on 2026-09-25**. Concepts only — retrieve the source article for exact steps. `Source:`
> URLs are canonical published docs (live `/docs/en/` form) and may be used to **cross-link** from
> generated articles. Archived/deprecated/unpublished docs are excluded.

## Table of Contents

- [Authoring on Web (Whatfix Studio extension)](#authoring-on-web-whatfix-studio-extension)
- [Supported protocols](#supported-protocols)
- [Browser compatibility](#browser-compatibility)
- [Deployment methods: JS Embed vs Browser Extension](#deployment-methods-js-embed-vs-browser-extension)
- [Extension deployment & management](#extension-deployment--management)
- [Mass deployment via endpoint-management tools](#mass-deployment-via-endpoint-management-tools)
- [Hosting models: Cloud, Self-Hosted, On-Premise](#hosting-models-cloud-self-hosted-on-premise)
- [Player Extension, MV3 & the deprecated Preview Extension](#player-extension-mv3--the-deprecated-preview-extension)
- [Advanced Customization (AC) code](#advanced-customization-ac-code)
- [Publishing on Web](#publishing-on-web)

---

## Authoring on Web (Whatfix Studio extension)

**Source:** https://support.whatfix.com/docs/en/how-to-install-the-whatfix-editor

On Web, **Whatfix Studio is a browser extension/plugin** used to create content (Flows, Smart Tips,
Beacons, etc.) by selecting elements directly on the target web application. Content creation is
supported only on specific browsers (see Browser compatibility).

## Supported protocols

**Source:** https://support.whatfix.com/docs/en/what-are-the-supported-protocols-in-whatfix-studio-1

Whatfix Studio supports content creation only on URLs using the **http** or **https** protocol
(this applies to the source URLs of Flows, Beacons, Smart Tips, and Launchers). Non-compliant URLs
must be updated, or content fetched from the CDN may not function.

## Browser compatibility

**Source:** https://support.whatfix.com/docs/en/which-browsers-does-whatfix-support-1

Browser support differs for **content creation** and **content deployment**. Content is created
only in **Google Chrome** and the new **Microsoft Edge (Chromium)**, through the Studio browser
plug-in. Deployed content is viewable as an overlay in all browsers, and end users need no add-on
or extension to see it. The standalone DAP Web browser-compatibility article is no longer
published, so retrieve the FAQ above (or the deployment articles) rather than asserting a
version matrix.

## Deployment methods: JS Embed vs Browser Extension

**Source:** https://support.whatfix.com/docs/en/integrating-whatfix-using-javascript (JS Embed) ·
https://support.whatfix.com/docs/en/integrate-whatfix-using-browser-extension (Extension)

Whatfix content is delivered to end users on Web in two ways:

- **JavaScript (JS) Embed** — the Whatfix code is embedded in the application's source. Preferred
  when you can modify the app's code. Supports **Subresource Integrity (SRI)** and per-app
  integrations (ServiceNow, PeopleSoft, Google Tag Manager, SAP SuccessFactors, Salesforce).
- **Browser Extension** — used when source-code embedding isn't possible; deploys content as an
  overlay via an end-user browser extension (Firefox, Chrome, Safari, Edge Chromium, IE).

The choice affects how content reaches users and how it's maintained; some applications switch
between methods (e.g. **browser extension → JS Embed for SAP SuccessFactors**,
https://support.whatfix.com/docs/en/switch-from-browser-extension-to-js-embed-for-sap-successfactors).

## Extension deployment & management

**Source:** https://support.whatfix.com/docs/en/manage-extensions-on-the-whatfix-dashboard

When using browser extensions, the Whatfix Dashboard generates and manages them. Options include:
the **Whatfix Store** (recommended hosting,
https://support.whatfix.com/docs/en/setting-up-the-whatfix-store-extension), a **Single Installer**
(.msi) covering multiple browsers, **mass deployment** (see below), **individual-user deployment**
via a hosted landing page, and **One-click Extensions on Internet Explorer**
(https://support.whatfix.com/docs/en/using-one-click-extensions-on-internet-explorer).

## Mass deployment via endpoint-management tools

**Source:** https://support.whatfix.com/docs/en/mass-deployment-of-the-browser-extension

For enterprise rollout, the extension can be mass-deployed through endpoint-management tooling —
**Microsoft Intune** (policy or MSI app), **SCCM** (MSI or PowerShell, with uninstall programs and
deployment-status views), **Group Policy Management Console (GPMC)**, and **Jamf** (Safari on
macOS; Chrome/Edge on macOS). Each has its own install/uninstall procedure (retrieve the specific
article).

## Hosting models: Cloud, Self-Hosted, On-Premise

**Source:** https://support.whatfix.com/docs/en/host-whatfix-content-on-premise ·
https://support.whatfix.com/docs/en/host-content-on-a-private-server

Whatfix content can be hosted on the **Whatfix cloud** (default), **Self-Hosted** (export a
Production Package and serve from your own server — Apache, Amazon S3, Microsoft Azure), or
**On-Premise** (all operations on private servers; Whatfix generates a separate Studio extension
that runs independently). The Self-Hosted export is documented as a **legacy** process: Whatfix
recommends browser-extension delivery instead, so content updates automatically. Separately,
**Self-Hosted Extensions** let you store the Whatfix extensions in your own **AWS or Azure** storage
bucket rather than the Whatfix cloud or a store
(https://support.whatfix.com/docs/en/self-hosted-extensions). The **Whatfix Store** serves Chrome
and Edge (Chromium) extensions from Whatfix's servers, so updates land in minutes rather than the
days a Chrome Store review takes. Some capabilities differ by hosting
model — confirm before asserting availability (e.g. self-hosted has its own analytics-enablement
path).

## Player Extension, MV3 & the deprecated Preview Extension

**Sources:** https://support.whatfix.com/docs/en/whatfix-player-extension ·
https://support.whatfix.com/docs/en/overview-of-manifest-v3-mv3-impact-on-whatfix

**Manifest V3 (MV3)** is a major update to the WebExtensions API for Chromium browsers (Chrome,
Edge, Opera) and Firefox. Under MV3, **injection of remote code is no longer allowed**, so custom
Advanced Customization (AC) code can't be previewed in Whatfix Studio's normal Preview mode. That
gap was first filled by a separate **Preview Extension**.

The **Whatfix Player Extension** now replaces both the **Preview** and **Production Extensions**
with one installation serving end users, authors and testers. **The Preview and Production
Extensions are deprecated**: they keep working without updates and are **sunset on November 30,
2026**, so new documentation should point to the Player Extension. What it displays is controlled
from the Dashboard by mapping each application environment to a stage configuration: **Draft,
Ready, Production** (development/testing), **Ready, Production** (UAT/staging) or **Production
only** (end users), with the lower stage taking precedence when versions differ. AC code changes
can be tested in the Testing environment through the Player Extension without publishing them.

**Whatfix Software Updates:** a new Whatfix software version reaches the Testing environment
first, with a **15-day testing period** before it updates Production (`software-release-management`).
**Software Version based Preview** (Beta; Player Extension and JS Embed only) lets authors preview
content against either version, and AI-generated release notes for software updates are Beta.

## Advanced Customization (AC) code

**Source:** https://support.whatfix.com/docs/en/access-code-editor

**Advanced Customization (AC) code** is optional code snippets for capabilities not available
through the Whatfix UI, edited in the **Code Editor**. **The Code Editor is not available for
accounts created after June 1, 2024**; on older accounts that still have AC code it is
**read-only**. AC code is why previewing needs the Player Extension (formerly the Preview
Extension) rather than Studio's Preview mode; an account with no AC code is unaffected.

## Publishing on Web

**Source:** https://support.whatfix.com/docs/en/enhanced-publishing-experience-1 ·
https://support.whatfix.com/docs/en/selective-publishing

Content goes live to end users only when published to **Production** (see CLM stages in
`dap-core.md`). The **Enhanced Publishing Experience** (Beta) and **Selective Publishing** let
authors push specific content/widgets rather than the whole account, with a summary of every
Dashboard change (including repository links and AC changes) before publishing; see also Publishing to Production best
practices (https://support.whatfix.com/docs/en/pushing-content-to-production-best-practices-1).
