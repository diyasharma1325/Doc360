# Whatfix Writing Guidelines — Agent Reference

## Brand Voice
- Approachable: use plain, conversational language
- Guiding: walk users through tasks step by step
- Inclusive: write for all users
- Transparent: explain how and why; no ambiguity

## The 5 C's
Write content that is **Clear** (first priority), **Consistent** (same term for same concept), **Contextual** (right place, right time), **Concise** (fewer words unless clarity suffers), and **Conversational** (speak to users as people).

---

## Sentences

- Use active voice only. Do not use passive voice.
- Write in present simple tense only. No future or conditional tense.
- Keep sentences under 30 words. Split or cut if longer.
- One idea or action per sentence.
- Use basic subject-verb structure.
- Avoid first-person plural. Use the product name instead.
  - ✗ One of the outputs we support is a slideshow.
  - ✓ One of the outputs Whatfix supports is a slideshow.
- Eliminate filler adjectives (easy, quickly, several, many, normally, usually). **Exception:** "automatically" is filler when it pads an instruction step, but keep it when it is load-bearing — i.e., describing system behavior that happens without user action (e.g., "Whatfix automatically syncs the roster every 24 hours.").
- Use lists when a sentence contains more than three items.
- Ensure parallel construction: all items in a list must use the same grammatical form (all noun phrases or all verb phrases).

### Verb Mood
| Mood | When to use | Example |
|---|---|---|
| Indicative | Explanations, facts, assertions | Whatfix is a Digital Adoption Platform. |
| Imperative | Instructions, procedures, list headings with user actions | Log in to the application. |
| Subjunctive | Suggestions | Whatfix recommends using a single language. |

---

## Words and Phrases to Avoid

| Avoid | Use instead |
|---|---|
| In order to | To |
| As well as | And |
| If you need to | To |
| Turn on | Enable |
| The application allows you to… | Use the application to… |
| Also known as | Called |
| Make a comparison | Compare |
| When/if you want to do | To do |
| any of the options | any option |
| Click on | Click |
| In many cases | Often |
| Hover over | Hover your cursor over |
| etcetera | and more |
| vice versa | the other way around |
| i.e., | that is |
| via | by / using |
| like | such as |
| utilize | use |
| a maximum of | up to |
| mouse cursor | cursor |
| navigate | go to |
| allows / allow / allowing / let / lets / letting | enables / enable / enabling |
| / | or |
| & | and |
| pop-up, pop-over (for dialog) | dialog box |
| Popups, popups (unhyphenated) | Pop-ups — always hyphenate. This is a spelling correction for this Whatfix content type, not a term ban: refer to Pop-ups by name using this spelling. |
| end users (noun) | users |
| you can (as a step/instruction opener) | start with the verb — but keep "You can" when stating a limit or permission (e.g., "You can add up to 100 domains.") |
| may (for possibility) | might |

- Do not use "Click Here" in link text. Use descriptive action text instead.
- Do not use "system" — it is a vague term. Do not use "the change" or "this change" without first stating what specifically changed. Notes about propagation delays or side effects must name the action and its consequence explicitly so the sentence reads as a standalone statement.
  - ✗ "The change may take up to 30 minutes to take effect across the system."
  - ✓ "Once you disable a domain, all learners authenticated through that domain lose access. This change may take up to 30 minutes to take effect."
- Do not use "You can" to start a *step/instruction* sentence. Remove it and start with the verb. **Exception:** "You can" is the standard, expected opener for stating a limit or permission — a fact about what the product allows, not an instruction to perform ("You can authorize up to 100 domains.", "You can enable this setting only when the workspace is on the Enterprise plan."). Use it for limits/permissions as needed; keep it out of ordinary step text.
- Do not use vague words: several, quickly, many, fine, this, these (without a clear antecedent).
- Avoid redundant word pairs (e.g., "successfully completed" → "completed").

---

## Headings

Written in Document360 terms: **article title** (the page's `<h1>`, never emitted as a
literal heading tag), **H2** (a major body section), **H3** (a sub-section under an H2), and
**accordion title** (the `<summary><strong>…</strong></summary>` text). There is no separate
"chapter"/"sub-header" tier — every heading in an article maps to one of these four.

### Capitalization
- **Article title and H2:** Capitalize the first letter of every word except conjunctions, articles, prepositions under four characters, and "to" in infinitives (unless they start the heading).
- **H3 and accordion titles:** Capitalize only the first word. Exception: field or button names used in the title retain their original casing.

### Naming Style
Naming style follows the article's type and depends on which element it is — it is never one
fixed rule for every heading:
- **Procedural article titles and accordion titles:** imperative verb-first (e.g., "Create a Flow," "Configure DAP Guidance on the Base Application"). A sequential, order-dependent accordion set may instead use "Step-N: [Phase Name]."
- **Overview article titles:** freeform — whatever reads most naturally for the topic ("What is X?", "Introduction to X," "Understand X," "X in Y," or a plain noun phrase like "X Analytics"). Not a fixed pattern; pick what fits.
- **Best Practices article titles:** "Best Practices for [Topic]." Accordion titles are imperative, action-first phrases, never a noun phrase or a question.
- **FAQ accordion titles:** the question itself, phrased as a direct question — never rephrased into a statement or imperative.
- **Release Notes:** the page title and per-feature `<h2>` follow the fixed formats in the Release Notes structure spec (e.g., "Qn Rn YYYY [Product] Release"; the feature name for the `<h2>`); the fixed section labels "What is new?", "Why does it matter to me?", and "How do I do this?" are used verbatim.
- **General H2/H3 section headings** (not covered by a type-specific rule above): use nouns, not imperative verbs or gerunds (-ing words) — e.g., "Text Insets," not "Inserting Text."

### General
- Punctuation: avoid it in general H2/H3 section headings (commas permitted when required), but question marks are required where the naming style above calls for a question (FAQ accordion titles, "What is X?"-style Overview titles, the Release Notes fixed labels).
- Acronyms are allowed in a heading, title, or accordion title when they are the established name of a product, feature, or industry term — typically introduced with the full term followed by the acronym in parentheses on first use (e.g., "Whatfix Service Level Agreement (SLA)," "Learning Management Systems (LMS)," DAP, SCORM). Do not invent new acronyms or abbreviate a term that doesn't already have a standard short form.

---

## Lists

### Bulleted Lists
- Introduce with a sentence ending in a colon.
- Keep all items consistent: all phrases or all complete sentences — do not mix.
- Use periods for all items or none (if mixing, use periods throughout for consistency).
- Do not use a vague, content-free bulleted-list intro like "The following list…" or a bare "…the following:" that names nothing specific — the lead-in must say what the list actually contains. This rule governs freeform bulleted-list intros only; it does not override the fixed lead-ins mandated elsewhere that happen to contain "the following" (e.g. "Use the following steps to…", "Expand the following accordions for more details:", Release Notes' "The following are the updates for [Product]:") — those are exempt.
- Do not create single-item bulleted lists.
- Do not exceed six or seven items; subdivide or consolidate if needed.
- Bulleted list items must not exceed one sentence.

**Phrase lists:** do not capitalize the first word (unless a proper noun); no period.
**Complete sentence lists:** capitalize the first word; end with a period.

### Ordered Lists
- Use Arabic numerals for the first level.
- Use English alphabets for the second level, then alternate.
- Indent each sublist.
- Do not use Roman numerals.
- Every numbered list item is a complete sentence and must end with a period.

---

## Punctuation

- Use a serial (Oxford) comma before the last item in a series of three or more.
- Use periods only at the end of bullets that are complete sentences.
- Add a colon after callout labels: **Note:**, **Info:**
- Do not add colons next to headings in troubleshooting articles (Issue, Probable Causes, Suggested Solutions).
- Avoid semicolons.
- Avoid exclamation marks.
- Do not use em dashes (—) anywhere in the article. Rewrite the sentence to avoid them.
- Avoid parentheses; use a Note callout instead for supplemental information.
- Use "and then" (not just "and") to indicate sequential actions.
  - ✗ Select Office VPN and enter the credentials and click Connect.
  - ✓ Select Office VPN and enter the credentials and then click Connect.
- Do not use more than one "and" per sentence.

---

## Paragraphs

- One idea per paragraph.
- Every sentence must relate to the central idea.
- Keep flow smooth; sentences should lead logically to the next.
- Break long paragraphs with subheadings.

---

## Addressing Readers

- Address the reader as **you**.
- Refer to multiple users as **users** (plural), not "a user" or "the user."
- Use **learners** (not "users") when referring to people interacting with Mirror content.
- Never use he/she. Use "you" or plural "users."
- Never use "content authors" or "authors" as standalone terms. Refer to all readers as **you**.

---

## Procedures

- Use imperative form only.
- State where the action takes place before describing the action (LSA rule).
- Write one action per step.
- Every step is a complete sentence and must end with a period.

### LSA Rule
Give instructions in this order: **Location → Selection → Action.**
- ✓ On the Order Settings page (location), in the Search drop-down menu (selection), click Orders (action).
- ✗ Click Orders in the Search drop-down menu on the Order Settings page.

*Note: Apply LSA only where it improves clarity. Skip it when it hinders readability.*

### Lead-in Sentences
- Use **"Use the following steps to…"** before every procedure.
- Use **"Expand the following accordions for more details:"** before accordion sections.

### Mutually Exclusive Option Lists
When a step requires the user to choose between mutually exclusive options (for example, options presented in a dialog box), do not use conditional sub-procedure format ("To do X, select Y, and then do Z"). Instead:
- Use **"Choose one of the following options:"** as the lead-in sentence. Do not include a location prefix.
- List each option as: **Option name**: Explanation sentence.

✓ Choose one of the following options:
- **Assign all content and tags to any of the following teammate**: Select a teammate from the **Teammate name** dropdown to transfer the content and tags.
- **Keep all content and tags with the teammate**: The content and tags remain associated with the deleted teammate.

✗ In the confirmation dialog box, select one of the following content handling options:
✗ To transfer the teammate's content, select **Assign all content and tags to any of the following teammate**, and then select the target teammate from the dropdown.

---

## Acronyms and Abbreviations

- Spell out the first occurrence of a non-standard or multi-meaning acronym, followed by the acronym in parentheses: bps (Bits per Second).
- Do not introduce acronyms for terms that appear only once.
- Do not use Whatfix-internal coined acronyms in external documents.
- Do not include periods within acronyms.
- Lowercase all spelled-out terms except proper nouns.
- Use possessive form only for acronyms referring to a person or organization (e.g., the CEO's mail).
- Abbreviate units of measurement only when paired with a number. Include a space between value and unit.
- Spell out KB, MB, GB when mentioned without a number; abbreviate when with a number.

---

## Capitalization (Body Text)

Capitalize:
- Proper nouns, book and chapter titles, product names
- UI labels, field names, file names, option names as they appear on screen
- References to menu names, options, and field names
- Abbreviations and acronyms (unless normally lowercase, e.g., bps)
- First letter of the first word in every sentence
- First letter of each cell in a table (unless it is a follow-on sentence)
- Both words of a hyphenated compound in a title or heading

Do not capitalize:
- Words for emphasis in body text
- The second word of a hyphenated compound outside of titles or headings (e.g., User-defined options)

---

## Tables

- Use tables for: procedures, menu/toolbar element descriptions, cause-effect relationships.
- Replace yes/no cells with check/cross icons.
- Use bold for all table headers.
- Use sentence capitalization for follow-on cell content (heading contains the start; cell completes it).
- Always end the table heading with a colon when using follow-on sentences.

---

## UI Elements

- All UI element names must be in **bold**.
- Do not append the element type when the name is sufficient.
  - ✓ Click **Create content**.
  - ✗ Click the **Create content** button.
- Do not include symbols adjacent to UI text.
  - ✓ Click **Set Visibility Rules**.
  - ✗ Click **Set Visibility Rules →**.
- Use "dialog box" — never "pop-up" or "pop-over."

### Input Controls
| Element | Definition | Usage |
|---|---|---|
| Checkbox | Square box to select or clear | Select the **Spaces** checkbox / Clear the **Spaces** checkbox |
| Combo box | Text box with list box attached | In the Font box, type or select the font. |
| Drop-down menu | Opens a list of options | Select **Inactive** using the drop-down menu. |
| Options / Radio button | Round button for mutually exclusive selection | Choose the **Portrait** option. |
| Toggle button | Changes a setting between two states | Enable the **Spaces** toggle. |
| Badge | Indicates status, notification, or event | See the **Deleted** badge next to the deleted content. |

### Navigational Components
| Element | Definition | Usage |
|---|---|---|
| More icon | Three-dots icon for a menu with more actions (e.g., on teammate rows). This is the canonical name — always use it even if a Flow export calls it something else. Do not use 'ellipsis icon', 'actions menu icon', 'options icon', 'three-dots icon', or 'More Options icon'. Bold only the name, never the word "icon": write `**More** icon`, NOT `**More icon**`. | Click the **More** icon, and then click **spaces**. |
| Tab | Labeled group of settings | Click the **View** tab. |

### Containers
| Element | Definition | Usage |
|---|---|---|
| Accordion | Vertically stacked list that shows/hides content on click | In the left panel, expand **Site Search**, and then click **Search Terms**. |

---

## Dates and Dimensions

- **Dates:** Month DD, YYYY — e.g., May 31, 2019.
- **Dimensions:** Use height (vertical) and width (horizontal). Do not use length or breadth.

---

## Contractions

- Use common contractions to maintain conversational tone: it's, you're, don't.
- Avoid ambiguous contractions: there'd, it'll, they'll.
- Do not mix contractions and spelled-out forms in the same UI text block.
- Do not form contractions from a noun and a verb (e.g., never "Whatfix'll").

---

## Usernames and Passwords

- Use **Credentials** to collectively refer to username and password.
- Use fictional names (John Doe, Jane Doe) as examples.
- Display passwords using * (asterisk).

---

## Accessibility (Core Rules)

- Write short sentences; aim for one verb per sentence.
- Spell out special characters (plus, and, etc.) — screen readers may misread symbols.
- Avoid directional terms (above, below, left, right) in instructions.

---

## Function vs. Feature

Describe what the user achieves, not which option to select.
- ✗ By configuring Commodity Mappings, you enable the system to automatically determine the contracted commodity.
- ✓ To determine the contracted commodities listed in the freight bill, configure Commodity Mappings.

---

## Hyphenated Words (Common Reference List)

The following compound words are always hyphenated. Correct the unhyphenated form wherever it appears in source material, PRD text, or flow exports — do not carry the source spelling into generated articles.

End-users (adjective only), In-house, Pop-up, Re-use, Re-create, Right-click, Left-click, Real-time (adjective only), Short-term, Step-by-step, On-screen, Smart-Tip

