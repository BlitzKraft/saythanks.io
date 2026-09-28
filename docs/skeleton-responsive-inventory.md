# Skeleton responsive style inventory

`normalize.css` loads first, Skeleton second, and `saythanks.css` last. Keep Skeleton's base layout and typography, with site-specific overrides in the last stylesheet. This inventory covers every section of the bundled Skeleton stylesheet; it is not a replacement framework.

| Skeleton section | Decision | Reason / site usage |
| --- | --- | --- |
| Grid (`.container`, `.column(s)`, numbered widths, offsets) | Keep 400/550px grid breakpoints and twelve-column widths/offsets. Correct templates to use actual grid classes. | The base container, home row, inbox links and thanks page use the grid. The old `sixteen columns` isn't defined by Skeleton; applying `twelve columns` prevents a 100%-wide float plus a 4% left margin. The 775px override intentionally stacks page-specific controls and widens the container on small screens; don't change desktop sizing wholesale. |
| Base (`html`, `body`) | Keep root 62.5% / 1.5em body proportions. | Site `rem` sizing assumes 10px per `rem` at the default browser font size. Browser zoom still works. |
| Typography (`h1`–`h6`, `p`) | Keep existing mobile/desktop heading scale and paragraph rhythm. | The site's mobile header overrides the default large heading at 775px. |
| Links | Keep default color rules; add visible focus treatment in site CSS. | Site green links and white X/Facebook SVGs depend on stronger, later selectors. Do not globally recolor them. |
| Buttons | Replace fixed 38px height, 11px text and forced single-line layout with 44px minimum, readable 13px text and wrapping. Retain primary/hover colors. | Longer sign-in/record/send labels must fit small screens and larger text; the editor toolbar keeps its explicit compact override. |
| Forms (`input`, `textarea`, `select`, `label`, `fieldset`, radios) | Use flexible 44px minimum controls; retain native select/radio appearance. Restore focus indication; keep site text inputs at 16px or larger. | Avoid clipped text and iOS input zoom. The byline remains 24px. The audio picker input is visually hidden but keyboard reachable, and its visible label receives its focus ring. |
| Lists | Keep existing desktop bullets, nesting and spacing; stop compounded font shrinking for nested lists on mobile. | Long inbox settings lists should remain legible on narrow screens. |
| Code (`code`, `pre > code`) | Wrap long inline tokens; give preformatted code a local horizontal scroller. | Preserve formatting without forcing the whole page wider. |
| Spacing | Keep component margins. | Page flow depends on the existing Skeleton spacing. |
| Utilities (`.u-full-width`, `.u-max-full-width`, pull floats) | Make full-width truly 100%; retain max-width-only and float utilities. | The badge controls and byline actually use full-width. The remaining utilities are safe to keep for templates or future use. |
| Tables | Keep borders, alignment and colors. Restrict row-hover styling to fine pointer devices; scroll the archived table locally at mobile widths. | Avoid sticky touch hover and page-level scrolling while keeping the desktop table familiar. |
| Misc (`hr`) and clearing (`.container:after`, `.row:after`, `.u-cf`) | Keep unchanged. | Floated columns and page layout need clearing; dividers match existing pages. |
| Empty media-query stubs | Remove. | No declarations, so no effect on any viewport. |

## Manual validation matrix

Compare the home, note form, inbox, archived inbox, shared note and thanks pages at 320, 375, 390, 550, 775 and 1024+ CSS pixels, plus a landscape phone width. Check document scroll width, local table/editor scrolling, heading wrapping, all buttons and the byline, keyboard focus, audio-picker activation and the X/Facebook icon colors. Test Android Chrome and iOS Safari on physical devices if available; Chromium mobile emulation cannot prove native iOS file-picker or Safari rendering behavior. Authentication-dependent inbox pages require a signed-in test account.