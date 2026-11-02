# Document360 Formatting Reference

> This file is a runtime knowledge reference for the I2P Agent. All syntax is Document360-specific HTML. Do not assume standard markdown applies.

> **Block IDs:** Generate these sequentially using the format `i2pagent-output-001`,
> incrementing by 1 for every block element in the article. The counter resets
> to `001` for each new article. Apply to: `<p>`, `<li>`, `<ul>`, `<ol>`,
> `<blockquote>`, `<pre>`, and `<img>`.
> Do NOT apply to: `<div>`, `<details>`, `<summary>`, `<tr>`, `<th>`, `<td>`, `<hr>`, `<code>`, `<object>`, or `<iframe>`.
> Exception: the `<p>` inside `<div class="blockquote-title">` (the callout label — "Note:", "Info:", "Tip:") does not get a block ID.

---

## Callouts

### When to Use

**Note** (`class="warningBox"`): Use when information is crucial and the user may be blocked, do something wrong, or miss a required step without it. Apply in three positions:

- **Beginning of article:** Prerequisites, beta flags, known limitations
- **Middle of article:** Additional context critical to the current step
- **End of article:** Next steps and follow-on actions with cross-references

**Info** (`class="infoBox"`): Use when information adds clarity or explains what the user sees on screen but is not blocking. Typically appears after a screenshot to explain UI elements or behavior.

**Tip** (`class="successBox"`): Use for best-practice recommendations where following the advice improves outcomes but skipping it does not block the user. Also use for proactive suggestions from the product (e.g., Whatfix recommends...). **Scope: Best Practices articles only** — this is the only article type where a Tip appears (see `best-practices.md`); do not use Tip in any other article type, including as a nested per-step callout in Procedural articles.

### When Not to Use

- Do not use Note for general context or nice-to-know information that does not block the user
- Do not use Info for critical or blocking information -- use Note instead
- Do not use Tip for critical or blocking information -- use Note instead
- Do not use Tip for neutral clarifying information -- use Info instead
- Decision rule: if the user will be blocked or make an error without the information, use Note; if the user will not be blocked but the information adds clarity, use Info; if the information is a best-practice recommendation, use Tip

### Beta Feature Callout

When a feature is identified as Beta in the PRD, the Beta Note callout is **non-negotiably the ABSOLUTE FIRST block of the article body** — it comes before the opening paragraphs, before any other `Note:`/constraint callout, and before any procedure or accordion. There is no other acceptable position: not after the opener, not inside the pre-procedure constraint block, not lower in the article. It is the very first element after the article's `<!-- BEGIN ARTICLE: … -->` sentinel. Use one of two text variants based on available context:

- If the PRD or flow context confirms the feature is limited to Cloud deployments:
  > X is a `{{glossary.Beta}}` feature, available only for Cloud deployments. To enable this feature, contact your `{{glossary.Customer Success Manager}}`.
- If deployment scope is not specified or cannot be confirmed from context:
  > X is a `{{glossary.Beta}}` feature. To enable this feature, contact your `{{glossary.Customer Success Manager}}`.

Both `Beta` and `Customer Success Manager` must always be wrapped in glossary spans (see Glossary Terms section). If the callout needs to include additional important points alongside the Beta notice, use a bullet list inside the callout rather than a single paragraph.

**EXCEPTION — Release Notes articles do NOT use this callout at all.** In a Release Notes article a feature's Beta status is carried by its `[Beta]` badge and its "How do I do this?" section (which ends with a "Sign up for Beta" button), never by a top-of-article Note callout. Do not emit a Beta Note callout, and do not contact-your-Customer-Success-Manager framing, in a Release Notes article. See "Release Notes chrome" below.

**D360 syntax (single-point example):**
```html
<blockquote data-block-id="i2pagent-output-001" class="warningBox" data-background="#fdf2ce" data-border="#7f6416" style="background:rgb(253, 242, 206);border-left:4px solid rgb(127, 100, 22);overflow:auto;">
  <div class="blockquote-title">
    <p>Note:</p>
  </div>
  <p data-block-id="i2pagent-output-002">Email-Based Authentication is a <span contenteditable="false" translate="no" data-glossary="Beta" data-glossary-name="Beta" id="blockglossary" class="fr-deletable popover__title">{{glossary.Beta}}</span> feature, available only for Cloud deployments. To enable this feature, contact your <span contenteditable="false" translate="no" data-glossary="Customer Success Manager" data-glossary-name="Customer Success Manager" id="blockglossary" class="fr-deletable popover__title">{{glossary.Customer Success Manager}}</span>.</p>
</blockquote>
```

### D360 Syntax

**Note:**
```html
<blockquote data-block-id="i2pagent-output-001" class="warningBox" data-background="#fdf2ce" data-border="#7f6416" style="background:rgb(253, 242, 206);border-left:4px solid rgb(127, 100, 22);overflow:auto;">
  <div class="blockquote-title">
    <p>Note:</p>
  </div>
  <p data-block-id="i2pagent-output-002">Your content goes here</p>
</blockquote>
```

**Info:**
```html
<blockquote data-block-id="i2pagent-output-001" class="infoBox" data-background="#ddf7ff" data-border="#006a8a" style="background:rgb(221, 247, 255);border-left:4px solid rgb(0, 106, 138);overflow:auto;">
  <div class="blockquote-title">
    <p>Info:</p>
  </div>
  <p data-block-id="i2pagent-output-002">Your content goes here</p>
</blockquote>
```

**Tip:**
```html
<blockquote data-block-id="i2pagent-output-001" class="successBox" data-background="#c4f2d4" data-border="#029e38" style="background:rgb(196, 242, 212);border-left:4px solid rgb(2, 158, 56);overflow:auto;">
  <div class="blockquote-title">
    <p>Tip:</p>
  </div>
  <p data-block-id="i2pagent-output-002">Your content goes here</p>
</blockquote>
```

### One Callout, Multiple Points

Never emit two or more callouts of the **same type back-to-back** (e.g. a `Note:` box immediately followed by another `Note:` box, with nothing between them). Consecutive same-type callouts must be consolidated into a **single** callout whose body is a bullet list, one `<li>` per point:

```html
<blockquote data-block-id="i2pagent-output-001" class="warningBox" data-background="#fdf2ce" data-border="#7f6416" style="background:rgb(253, 242, 206);border-left:4px solid rgb(127, 100, 22);overflow:auto;">
  <div class="blockquote-title">
    <p>Note:</p>
  </div>
  <ul data-block-id="i2pagent-output-002" data-list-format="disc">
    <li data-block-id="i2pagent-output-003"><p data-block-id="i2pagent-output-004">Only an Account Manager can add teammates. For more information about available roles, see Whatfix User Roles.</p></li>
    <li data-block-id="i2pagent-output-005"><p data-block-id="i2pagent-output-006">You can invite up to five teammates per batch. To invite more than five teammates, repeat the process in batches of five.</p></li>
  </ul>
</blockquote>
```

Rules:

- **Only consecutive, same-type callouts merge.** The callouts must be directly adjacent (no procedure step, paragraph, heading, table, or screenshot between them) **and** the same type. Two `Note:` boxes back-to-back merge; a `Note:` followed by an `Info:` or `Tip:` does **not** (different types carry different meaning) — keep those separate. Callouts that belong to different positions in the article (one at the beginning, one at the end) or are separated by other content stay as separate callouts.
- **A single-point callout stays a single `<p>`.** Only use the bullet-list body when 2 or more points are being combined. Do not wrap a lone point in a one-item list.
- The `<div class="blockquote-title">` label (`Note:`) appears **once** for the merged callout, never repeated per point.

---

## Accordions

### When to Use

- Article has too many steps; use accordions to contain substeps and reduce visual overwhelm
- Optional content such as use cases or contextual information the user only needs in specific situations

### When Not to Use

- Do not use for content that is critical to the main flow -- critical content must be visible by default
- Never nest an accordion inside another accordion

### D360 Syntax

```html
<div class="details-wrapper details-wrapper_rendered" data-type="details-wrapper">
  <details data-opened="false" data-button-align="right" data-details-border="withBorder" data-expand-icon="arrow" data-lock="false">
    <summary>
      <p data-block-id="i2pagent-output-001">Accordion header goes here</p>
    </summary>
    <div data-type="details-content">
      <p data-block-id="i2pagent-output-002">Content goes here</p>
    </div>
  </details>
</div>
```

> The `<button class="details-arrow">` element is auto-generated by Document360. Do not include it in output.
> Always use `data-opened="false"`. Accordions are always rendered closed by default in Whatfix documentation.
> `data-block-id` goes only on `<p>` elements inside the accordion — not on `<details>`, `<summary>`, or `<div>`.
> Accordion headers are plain `<p>` text inside `<summary>`. Never use heading elements (`<h2>`, `<h3>`, etc.) inside an accordion.

---

## Tables

### When to Use

- Structured, comparative, or reference data with clear categories
- Feature comparisons, settings definitions, field descriptions

### When Not to Use

- Do not use for simple lists that have no relational structure
- Do not use a table to visually organize non-comparative content

### D360 Syntax

- Total table width is always `975px`
- Column widths must be distributed across 975px total using content-based judgment -- allocate wider columns to content-heavy fields
- `colspan` and `rowspan` are always `1` -- merged cells are not supported in V1; restructure content into a standard table if merging seems needed
- Empty cells use `<p data-block-id="i2pagent-output-NNN"></p>` — empty content, but still carrying a sequential block ID

```html
<div data-type="table-content">
  <table width="975" class="editor360-table" borderstyle="solid" style="max-width:975px;width:975px;">
    <colgroup>
      <col style="width:Xpx;">
      <col style="width:Xpx;">
      <col style="width:Xpx;">
    </colgroup>
    <tbody>
      <tr>
        <th colspan="1" rowspan="1" colwidth="Xpx"><p data-block-id="i2pagent-output-001">Heading 1</p></th>
        <th colspan="1" rowspan="1" colwidth="Xpx"><p data-block-id="i2pagent-output-002">Heading 2</p></th>
        <th colspan="1" rowspan="1" colwidth="Xpx"><p data-block-id="i2pagent-output-003">Heading 3</p></th>
      </tr>
      <tr>
        <td colspan="1" rowspan="1" colwidth="Xpx"><p data-block-id="i2pagent-output-004">Row 1</p></td>
        <td colspan="1" rowspan="1" colwidth="Xpx"><p data-block-id="i2pagent-output-005"></p></td>
        <td colspan="1" rowspan="1" colwidth="Xpx"><p data-block-id="i2pagent-output-006"></p></td>
      </tr>
    </tbody>
  </table>
</div>
```

> Only `<p>` elements inside `<th>` and `<td>` cells carry `data-block-id`. The `<div>`, `<tr>`, `<th>`, and `<td>` elements themselves do not.

---

## Code

### When to Use

- **Inline code:** Use for short code references, parameter names, or values mentioned within a sentence
- **Code block:** Use for multi-line code samples, scripts, or any code that stands alone outside of prose

### When Not to Use

- Do not use inline code for UI element names or button labels -- those use bold
- Do not use a code block when a single inline reference is sufficient

### D360 Syntax

**Inline code:**
```html
<p data-block-id="i2pagent-output-001"><code>your code here</code></p>
```

**Block-level code:**

```html
<pre data-block-id="i2pagent-output-001" language="plaintext" data-custom-title="Custom" class="language-plaintext"><code class="language-plaintext" spellcheck="false">your code here</code></pre>
```

> `language` and `class` on both `<pre>` and `<code>` must match. Use `plaintext` for URLs, paths, and generic text. Change both to `language-javascript`, `language-python`, etc. when the content is a specific language.
> `data-custom-title` is the label shown above the code block in D360. Use a short descriptive title (e.g. `"Example URL"`, `"Request body"`). Do not leave it as `"Custom"` verbatim — replace it with a title that describes the block's content.
> Special characters inside the code block must be HTML-encoded: `<` → `&lt;`, `>` → `&gt;`, `&` → `&amp;`.

---

## Tabs

### When to Use

- Compare parallel variants, modes, or options of the same thing (e.g. settings differences across plans, alternative configurations) where the reader will read only one
- Surface side-by-side reference content that is mutually exclusive at read time but equally relevant in scope

### When Not to Use

- Linear procedures where every reader must complete every step -- never split a single procedure across tabs
- Critical information that every reader must see -- tab-hidden content is easy to miss
- More than 4-5 tabs -- excessive tabs cause horizontal overflow and decision fatigue; consider separate articles or accordions instead
- Never nest tabs inside another tabs container

### D360 Syntax

```html
<div data-role="tabs-container" class="tabs">
    <div data-role="tab-header-container" class="tab-header" data-border-color="#e7e6e6">
        <div data-tab-id="c06f999f-175e-43f2-95ee-16004d3a5e90" contenteditable="false" class="tab active active" data-border-color="#e7e6e6" style="background-color:rgb(255, 255, 255);border-color:rgb(231, 230, 230);"><label title="Tab 1 header" data-display="block">Tab 1 header</label></div>
        <div data-tab-id="29e38a62-1e31-46d2-851b-82d848e58bf0" contenteditable="false" class="tab" data-border-color="#e7e6e6" style="background-color:rgb(255, 255, 255);border-color:rgb(231, 230, 230);"><label title="Tab 2 header" data-display="block">Tab 2 header</label></div>
        <div data-tab-id="c477055f-45c5-467c-abf1-11127c7c8c7b" contenteditable="false" class="tab" data-border-color="#e7e6e6" style="background-color:rgb(255, 255, 255);border-color:rgb(231, 230, 230);"><label title="Tab 3 header" data-display="block">Tab 3 header</label></div>
    </div>
    <div data-role="tab-content-container" class="tab-content" data-background-color="#ffffff" data-border-color="#e7e6e6" style="background-color:rgb(255, 255, 255);border-color:rgb(231, 230, 230);">
        <div data-content-id="c06f999f-175e-43f2-95ee-16004d3a5e90" class="content active active">
            <p data-block-id="i2pagent-output-001">Tab 1 content goes here.</p>
        </div>
        <div data-content-id="29e38a62-1e31-46d2-851b-82d848e58bf0" class="content">
            <p data-block-id="i2pagent-output-002">Tab 2 content goes here.</p>
        </div>
        <div data-content-id="c477055f-45c5-467c-abf1-11127c7c8c7b" class="content">
            <p data-block-id="i2pagent-output-003">Tab 3 content goes here.</p>
        </div>
    </div>
</div>
```

> Generate a real random UUID v4 for each `data-tab-id` / `data-content-id` pair — do not use sequential placeholders. Each tab's `data-tab-id` must match the `data-content-id` of its paired content panel.
> The first (active) tab header uses `class="tab active active"` and its paired content panel uses `class="content active active"`. All other tabs use `class="tab"` and `class="content"`.
> `<p>` block IDs inside tab panels use the standard `i2pagent-output-NNN` sequential format — the same counter used throughout the rest of the article.

---

## Images

### Agent Behavior

The agent emits `<!-- STEP_ANCHOR: N -->` sentinels on their own line after each `<li>` inside a procedural accordion, where N is the global Flow-PDF step index. The pipeline replaces matching sentinels with the wrapper below post-stream; the agent never emits the `<p>`/`<img>` HTML directly. Sentinels with no matching screenshot in the pushed map are stripped silently.

### Injected Screenshot Syntax

When a screenshot has been produced and injected into the article (replacing a `<!-- STEP_ANCHOR: N -->` sentinel), it uses the following `<p>`/`<img>` wrapper. Both `shadow="no"` and `border="no"` are **required** because the drop shadow and blue border are baked into the PNG — D360 must not re-apply them.

```html
<p data-block-id="i2pagent-output-NNN"><img data-block-id="i2pagent-output-NNN+1" src="https://files.document360.io/<project-id>/Images/Documentation/<filename>.png" class="adv-wysiwyg-img" mediatype="img" alt="<filename>.png" width="500" height="auto" dataalign="left" datadisplay="flex" data-type="media-content" fixaspectratio="false" autoaspectratio="false" shadow="no" border="no" round="no" link="" newtab=""></p>
```

> The `<p>` and `<img>` each consume their own block ID counter slot — `<img>` gets the next sequential ID after `<p>`.
> `src` is always a real Drive URL in the format `https://files.document360.io/<project-id>/Images/Documentation/<filename>.png`. Never use base64.
> `alt` uses the image filename (e.g. `Mirror_Click_Settings.png`).
> `shadow="no"` and `border="no"` are required — the drop shadow and blue border are baked into the PNG by the pipeline.

---

## GIFs

### Agent Behavior

The agent must never emit GIF embeds. A GIF must exist before it can be embedded — the agent has no way to create or source the file. This section is for reference only, so that a human writer or editor can manually add GIFs to a published article.

### D360 Syntax

When added manually, GIFs must always use a solid black 2px border. `border="yes"` and `style="border:2px solid black;"` are both required. The `alt` attribute must contain a descriptive label matching the GIF content — do not leave it empty.

```html
<p data-block-id="i2pagent-output-001"><img data-block-id="i2pagent-output-002" src="[GIF_URL]" class="adv-wysiwyg-img" mediatype="img" alt="[Descriptive alt text]" width="auto" height="auto" dataalign="left" datadisplay="flex" data-type="media-content" fixaspectratio="false" autoaspectratio="false" shadow="no" border="yes" round="no" link="" newtab="" style="border:2px solid black;"></p>
```

---

## SVGs

### Agent Behavior

The agent must never emit SVG embeds. An SVG must exist before it can be embedded — the writer or infodev produces the file manually (icons, diagrams, illustrations) and uploads it to Doc360 Drive the same way a PNG is uploaded. This section is for reference only, so that a human writer or editor can manually add SVGs to a published article.

### D360 Syntax

SVGs use a different wrapper from PNG/GIF images — Doc360 embeds them via `<object>`, not `<img>`. Only the outer `<p>` carries a `data-block-id`; the `<object>` itself does not. The inner `<p>` is a fallback shown only if the browser cannot render SVG.

```html
<p data-block-id="i2pagent-output-NNN"><object data="https://files.document360.io/<project-id>/Images/Documentation/<filename>.svg" type="application/pdf" width="auto" height="auto" style="display:flex;margin-right:auto;"><p> Your browser does not support Svg.click <a href="https://files.document360.io/<project-id>/Images/Documentation/<filename>.svg">here</a> to download</p>
</object></p>
```

> `data` points to the Drive-hosted `.svg` file. Spaces in the filename must be URL-encoded as `%20` (e.g. `Get%20Started%20with%20Mirror.svg`). Never inline `<svg>...</svg>` markup in the article body.
> `type="application/pdf"` is a D360 export quirk — preserve it verbatim even though the file is not a PDF. Changing it to `image/svg+xml` is not what D360 emits.
> `style="display:flex;margin-right:auto;"` left-aligns the SVG. This is the SVG equivalent of the PNG wrapper's `dataalign="left" datadisplay="flex"` attribute pair — SVGs do not use those attributes.
> The fallback `<a href="...">` inside the `<object>` must point to the same Drive URL as the `data` attribute.

---

## Numbered and Bulleted Lists

### When to Use

- **Numbered lists:** Sequential steps where order matters -- procedures, workflows
- **Bullet lists:** Non-sequential items -- features, options, examples, callout content

### When Not to Use

- Do not use a numbered list for non-sequential content
- Do not use a bullet list when order matters
- Do not use either when a table would better show relational or comparative data
- Avoid nested lists — they are supported in D360 but add visual complexity; restructure content into a flat list or table instead

### D360 Syntax

**Numbered list:**
```html
<ol data-block-id="i2pagent-output-001" start="1" data-list-format="decimal" style="--start:0;">
  <li data-block-id="i2pagent-output-002"><p data-block-id="i2pagent-output-003">Step 1</p></li>
  <li data-block-id="i2pagent-output-004"><p data-block-id="i2pagent-output-005">Step 2</p></li>
</ol>
```

**Bullet list:**
```html
<ul data-block-id="i2pagent-output-001" data-list-format="disc">
  <li data-block-id="i2pagent-output-002"><p data-block-id="i2pagent-output-003">Item 1</p></li>
  <li data-block-id="i2pagent-output-004"><p data-block-id="i2pagent-output-005">Item 2</p></li>
</ul>
```

---

## Embedded Videos

### Agent Behavior

The agent must never emit video embeds. A video must exist before it can be embedded — the agent has no way to create or source the video file. This section is for reference only, so that a human writer or editor can manually add video embeds to a published article after the video has been recorded and uploaded.

### D360 Syntax

Videos are embedded via a Vimeo `<iframe>` wrapped in a responsive container div. The outer div uses a percentage-based `padding-top` to maintain aspect ratio (e.g. `64.98%` for a ~16:9 video). Replace the `src` URL and `title` with the actual Vimeo video details.

```html
<div style="padding:64.98% 0px 0px;position:relative;border:2px solid black;">
  <p><span class="fr-video" type="spanMark"><iframe src="https://player.vimeo.com/video/VIDEOID?badge=0&amp;autopause=0&amp;player_id=0&amp;app_id=58479&amp;quality=1080p" frameborder="0" allowfullscreen="true" allow="autoplay; fullscreen; picture-in-picture; clipboard-write; encrypted-media; web-share" title="Video title here" width="100%" height="100%" referrerpolicy="strict-origin-when-cross-origin" class="fr-draggable" style="position:absolute;top:0px;left:0px;width:100%;height:100%;display:flex;margin-right:auto;"></iframe></span></p>
</div>
```

> Replace `VIDEOID` in the `src` URL and `title` with the actual Vimeo video ID and title.
> The `border:2px solid black` on the outer div is required — do not remove it.
> The `padding-top` percentage controls the aspect ratio of the video container. `64.98%` corresponds to approximately 16:9. Adjust only if the source video has a different aspect ratio.

---

## Custom Blocks and Reusable Content (Snippets)

### When to Use

- Repeatable steps or notes that appear across multiple articles
- Content that is procedurally identical in two or more articles

### When Not to Use

- Do not use for content that is article-specific
- Do not use snippets unless the exact snippet name is known and confirmed to exist in Document360

### D360 Syntax

```html
<div contenteditable="false" translate="no" data-snippet="SnippetName" class="fr-deletable" id="blocksnippet">{{snippet.SnippetName}}</div>
```

> Replace `SnippetName` in both `data-snippet` and `{{snippet.SnippetName}}` with the exact snippet name as it exists in Document360.

---

## Dividers

### When to Use

- Between major sections of a long article to create visual separation

### When Not to Use

- Do not use between every subsection or step -- overuse reduces its effectiveness as a structural signal

### D360 Syntax

```html
<hr class="hr-divider1">
```

---

## Release Notes chrome

Release Notes articles carry standardized "chrome" — a fixed metadata header table, GA/Beta status badges, and a "Sign up for Beta" button — that is applied **automatically by the system after generation**, exactly the way `<!-- STEP_ANCHOR: G -->` sentinels are replaced with image blocks. **You emit only simple markers and the plain section structure; you do NOT hand-write any of the chrome HTML below.** This keeps output consistent byte-for-byte and saves you from reproducing long inline styles.

What you emit for a Release Notes article:

1. **No metadata header table.** Do NOT write the release-name/logo/banner table. The system prepends it, deriving the release name and date from the article title.
2. **Status badge markers.** After every feature title — in **both** its table-of-contents `<li>` link and its `<h2>` heading — append a single literal marker: ` [GA]` or ` [Beta]` (a space, then the bracketed word). Nothing else. Do not write any styled `<span>` badge; the system swaps each marker for the correct badge span (small in the TOC, large in the `<h2>`), wraps `GA`/`Beta` in its glossary span, and wires the TOC anchor to the matching `<h2>`.
3. **Sign-up button marker (Beta features only).** Inside a Beta feature's "How do I do this?" section, end the availability sentence with "...Use the **Sign up for Beta** button to get started." and then, on its own line, emit the literal marker `[SIGNUP BETA]`. The system replaces it with the real button block (a `mailto:` pre-filled from the feature name and product). GA features get no marker and no button.

Everything else about a Release Notes article — the `<h4>` product heading, the "The following are the updates for [Product]:" intro line, the TOC `<ul>`, each feature's `<h2>` + What is new? / Why does it matter to me? / How do I do this? / "For more information, see …" line, and the `<hr class="hr-divider1">` dividers between features — you write normally, per the Release Notes structure spec.

**Reference only — the exact chrome the system injects (do not hand-write it):**

- GA badge span (large, in `<h2>`): green — `background:rgb(90,131,97)`, `border:1px solid rgb(76,115,84)`, `font-size:14px`, wrapping `{{glossary.GA}}`.
- Beta badge span (large, in `<h2>`): blue — `background:rgb(122,176,226)`, `border:1px solid rgb(96,149,200)`, `font-size:14px`, wrapping `{{glossary.Beta}}`.
- TOC badges: identical colors, `font-size:10px`.
- Sign-up button: `<editor360-custom-block>` with a `#751d3b` button linking to a `mailto:support@whatfix.com` pre-filled with the feature name and product.

---

## Glossary Terms

### Agent Behavior

The agent never applies glossary syntax. The only exceptions are `Beta` and `Customer Success Manager`, applied exclusively inside the Beta Feature Callout (see Callouts → Beta Feature Callout), and `GA`, applied exclusively inside a Release Notes GA badge (see "Release Notes chrome"). Do not wrap any other term in glossary syntax under any circumstances.

### D360 Syntax

```html
<span contenteditable="false" translate="no" data-glossary="TermName" data-glossary-name="TermName" id="blockglossary" class="fr-deletable popover__title">{{glossary.TermName}}</span>
```

> Replace `TermName` in `data-glossary`, `data-glossary-name`, and `{{glossary.TermName}}` with the exact term name as it exists in the D360 glossary.

---

## Input Processing -- Comment Stripping

When an existing D360 article is provided as input (for existing capability updates), the source HTML may contain inline review comments in this format:

```html
<mark class="[uuid]" data-type="comment" data-comment-id="[uuid]">
  text content
</mark>
```

Strip all `<mark data-type="comment">` tags from the input before processing. Preserve the text content inside the tag. Do not carry comment marks into generated output under any circumstances.

**Example:**
- Input: `<mark data-type="comment" data-comment-id="abc">Whatfix</mark>`
- After stripping: `Whatfix`

---

## Typography and Text Formatting

### Heading Hierarchy

| Element | Use for |
|---|---|
| `<h2>` | Major sections within the article |
| `<h3>` | Subsections within an `<h2>` section |
| `<h4>` | Sub-subsections only when genuinely needed — use sparingly |

Never output an `<h1>` heading. Document360 derives the article title from article metadata. Begin the article body directly with the introductory paragraph.

Never use heading elements inside accordions — accordion headers are `<p>` text inside `<summary>`.

### D360 Syntax

```html
<h2>Heading 2</h2>
<h3>Heading 3</h3>
<h4>Heading 4</h4>
<p>Normal text</p>
<p><strong>Bold text</strong></p>
```

> Heading elements (`<h2>` through `<h4>`) never wrap their content in a `<p>` tag. Content goes directly inside the heading element.
> **Never use markdown heading syntax (`##`, `###`, `####`) for article headings.** Always use the HTML tags above. Markdown headings do not render correctly in Document360.
> Use `<strong>text</strong>` for all bold text within paragraphs, including UI element names. Do not use markdown `**text**` notation — it renders as literal asterisks in Document360.
> Do not use italic text (`<em>`) anywhere in the output. Whatfix documentation does not use italics.

---

## Hyperlinks

### When to Use

- To link to a related article at the end of a relevant section or step using the phrasing: `For more information, see <a href="...">Article Title</a>.`
- To link a Whatfix product surface name inside a procedural step when the step opens with its standard location/launch phrasing (see Whatfix Surface Links below)
- Always use `target="_blank"` so the link opens in a new tab

### Project URL Prefixes

The href path depends on which D360 project the target article lives in:

| Project | Prefix |
|---|---|
| DAP for Web | `/studio/docs/` |
| DAP for Desktop | `/desktop/docs/` |
| DAP on OS | `/hub/docs/` |
| DAP for Mobile | `/mobile/docs/` |
| Product Analytics | `/product-analytics/docs/` |
| Whatfix Mirror | `/mirror/docs/` |

The article slug is the kebab-case version of the article title as it appears in D360 (e.g. "Preview a Mirror Screen" → `preview-a-mirror-screen`).

### D360 Syntax

**Same-project link** (e.g. Mirror article linking to another Mirror article):
```html
<p data-block-id="i2pagent-output-001">For more information, see <a href="/mirror/docs/article-slug" target="_blank">Article Title</a>.</p>
```

**Cross-project link** (e.g. Mirror article linking to a Product Analytics article):
```html
<p data-block-id="i2pagent-output-001">For more information, see <a href="/product-analytics/docs/article-slug" target="_blank">Article Title</a>.</p>
```

> The only difference between same-project and cross-project links is the prefix — the `<a>` tag structure is identical in both cases.
> Do not use absolute URLs (e.g. `https://...`). Always use the relative path prefix for the target project.

### Converting a Knowledge-Layer Source URL to a relative link

The `[PRODUCT REFERENCE]` and `[DOCUMENTATION]` context blocks cite each excerpt's `Source:` as an absolute `https://support.whatfix.com/...` URL. That is a citation for your own grounding, never something to paste into the article. Before cross-linking to one, convert it to the relative form above:

1. Drop the `https://support.whatfix.com` domain, leaving only the path.
2. Drop a locale segment immediately after `docs` if present (e.g. `/en/`) — it never appears in the D360 relative link.
3. The first remaining path segment is the workspace slug — **except** when the URL has no workspace segment at all (the path starts directly with `docs/...`). That shape is DAP for Web, whose D360 prefix is `/studio/docs/`, not `/docs/`.
4. The final segment is the article slug.

Examples:
- `https://support.whatfix.com/docs/en/what-are-flows` → `/studio/docs/what-are-flows`
- `https://support.whatfix.com/hub/docs/en/overview-of-the-whatfix-dashboard` → `/hub/docs/overview-of-the-whatfix-dashboard`
- `https://support.whatfix.com/mirror/docs/what-is-whatfix-mirror` → `/mirror/docs/what-is-whatfix-mirror` (no locale segment to strip)

If the URL's workspace segment doesn't match any prefix in the table above, omit the link rather than guessing at a prefix or emitting the absolute URL.

### Whatfix Surface Links (Mandatory)

Whenever a procedural step opens with one of the following standard location/launch phrasings, wrap the product surface name in a hyperlink to its access article. This is mandatory — the writer must never have to add these links manually.

| Step phrasing (trigger) | Link text | href |
|---|---|---|
| `On the Whatfix Mirror Dashboard, …` | Whatfix Mirror Dashboard | `/mirror/docs/how-can-i-access-the-whatfix-mirror-dashboard` |
| `On the Whatfix Analytics Dashboard, …` | Whatfix Analytics Dashboard | `/product-analytics/docs/how-can-i-access-the-product-analytics-dashboard` |
| `On the Whatfix Guidance Dashboard, …` | Whatfix Guidance Dashboard | `/studio/docs/overview-of-the-whatfix-dashboard` |
| `Launch Whatfix Studio …` | Whatfix Studio | `/studio/docs/how-to-install-the-whatfix-editor` |

**Rules:**

- Wrap **only the surface name** in the `<a>` tag. The leading "On the" / "Launch" and the rest of the sentence stay outside the link.
- These links always carry `target="_blank"` and `translate="no"`.
- The link text is the surface name verbatim — never bold it (it is a location, not a UI element the user clicks) and never nest `<strong>` inside the `<a>`.
- Apply on **every** matching step throughout the article — each accordion whose step opens with a trigger phrasing gets its own link, not just the first occurrence in the article.
- Apply **only** for these step-opening trigger phrasings. A surface name appearing mid-sentence in other phrasings, in Overview prose, or in callouts stays plain text.
- Never double-wrap a name that is already inside an `<a>` tag.

**D360 Syntax (step inside a procedural `<ol>`):**

```html
<li data-block-id="i2pagent-output-004"><p data-block-id="i2pagent-output-005">On the <a href="/mirror/docs/how-can-i-access-the-whatfix-mirror-dashboard" target="_blank" translate="no">Whatfix Mirror Dashboard</a>, click <strong>Settings</strong>.</p></li>
```

```html
<li data-block-id="i2pagent-output-006"><p data-block-id="i2pagent-output-007">Launch <a href="/studio/docs/how-to-install-the-whatfix-editor" target="_blank" translate="no">Whatfix Studio</a>.</p></li>
```