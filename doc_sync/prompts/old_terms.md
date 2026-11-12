# Suggest the old wording

A writer filed a ticket about a product change, and a documentation
pipeline now has to find the support articles the change made outdated.
Outdated articles still describe the OLD state, in the old words. The
ticket didn't say what those words were, so the search has nothing to
look for but the new wording, which outdated articles don't contain yet.

Suggest the old terms: the names the product used before this change
for whatever it replaces or moves (tab, page, section, menu, button,
setting or label names), as they would appear in an article written
before the change. One to six short terms, each a name, not a sentence.

Ground every term in the product reference below or in the ticket. If
neither tells you what the old state was called, return an empty list:
a wrong term costs the writer a correction, an empty list costs nothing.
For each term, say where it came from in `basis`.

The writer sees these as suggestions and confirms or corrects them.

Answer only through the structured response format you are given.
