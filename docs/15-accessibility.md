# Accessibility

Making the project usable by people with different abilities — vision,
hearing, motor, cognitive. Much of it also makes things better for
everyone (readable text, remappable keys, clear errors).

## Does this apply?

Decide in Phase 0 and delete what doesn't apply:

- **No user interface** (library, background script, agent with no
  screen): replace this doc with the "Not needed" stub (see `AGENTS.md` →
  Doc status; keep the file so references stay valid) and add "no user interface — accessibility not
  applicable" to `00-vision.md` → Non-goals.
- **App or website:** keep "Apps and websites", delete "Games".
- **Game:** keep "Games", delete "Apps and websites". (If the game has
  heavy menus or a launcher, keep both.)

Record the target as an NFR in `01-requirements.md` (e.g. "NFR3:
meets WCAG 2.2 AA" or "NFR3: meets the Games checklist below").

## Apps and websites — WCAG 2.2 level AA

The standard is the [Web Content Accessibility Guidelines
(WCAG) 2.2](https://www.w3.org/TR/WCAG22/), level AA. The checklist below
covers the items that matter most for a small project:

- [ ] **Keyboard:** everything works with a keyboard alone, in a sensible
      order, with no place the focus gets stuck
- [ ] **Visible focus:** you can always see which element has keyboard
      focus
- [ ] **Contrast:** text at least 4.5:1 against its background (3:1 for
      large text and for icons/control borders)
- [ ] **Not colour alone:** colour is never the only way information is
      shown (add text, an icon, or a pattern)
- [ ] **Text alternatives:** meaningful images have alt text; decorative
      ones are marked as decorative
- [ ] **Labels:** every input has a visible label; errors say what's wrong
      and how to fix it
- [ ] **Resizable text:** usable at 200% zoom without losing content
- [ ] **Motion:** respects the system "reduce motion" setting; nothing
      flashes more than 3 times per second
- [ ] **Target size:** clickable targets at least 24×24 px
- [ ] **Structure:** headings, lists, and buttons use the proper elements,
      so screen readers can navigate them

## How to test

Automated tools catch only part of the problems — always combine them with
the manual checks. Record results in `12-manual-tests.md`.

| Check | How |
|---|---|
| Keyboard-only | Unplug or ignore the mouse and complete the main tasks |
| Contrast | A contrast checker (e.g. WebAIM's) on text and controls |
| Colour blindness | A colour-blindness simulator on screenshots (several types) |
| Screen reader (apps/web) | A quick pass with Narrator or NVDA on Windows |
| Zoom (apps/web) | Browser or system zoom to 200% |
| Automated scan (web) | axe DevTools or Lighthouse's accessibility audit |

## Checklists

### Every change to the user interface
- [ ] Relevant checklist items above still hold for the changed screens
- [ ] New colours meet contrast; new controls work by keyboard

### End of each phase
- [ ] Full test pass from the table above, recorded in
      `12-manual-tests.md`
