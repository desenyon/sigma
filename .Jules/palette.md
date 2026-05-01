## 2026-04-22 - Keyboard shortcut clarity in the Ink shell
**Learning:** Keyboard guidance in a terminal app becomes noisy when every pane advertises the same shortcuts and visually ambiguous when unfocused panes keep accent styling.
**Action:** Keep shortcut hints context-aware to the active pane, render inline keys in a distinct bold treatment, and dim inactive panes so keyboard focus is unambiguous.
## 2024-03-24 - Consistent Keyboard Shortcut Styling & Contextual Prompt Hints
**Learning:** Terminal UI users depend heavily on visual consistency for keyboard navigation cues. We found that pagination shortcuts (`[ ]`) were rendered as plain text in the workspace component, missing the application's established pattern (`<Text color="white" bold>`) for keybindings, which reduced discoverability. Furthermore, static action hints like "Enter to run" create confusing states when an action is actively running (`busy=true`) and input is temporarily disabled.
**Action:** Always wrap inline keyboard shortcut references in a consistent highlight pattern (`<Text color="white" bold>` against `gray` helper text) by updating string-based layout rows to support rendering arbitrary `ReactNode`s when necessary. Additionally, conditionally render interactive hints (like "Enter to run") so they only appear when the action is actually available to the user.
## 2026-05-01 - [Conditionally hide action hints]
**Learning:** Interactive action hints (e.g., 'Enter to run') can cause visual noise and user confusion if shown when the user cannot actually perform the action, such as when the relevant input pane is not focused.
**Action:** Conditionally hide interactive action hints based on the focus state of the relevant input element or pane.
