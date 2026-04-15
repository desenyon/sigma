## 2024-04-15 - Context-Aware Terminal Shortcuts
**Learning:** In terminal UIs with multiple focusable panes (like Ink), static helper text at the bottom often shows shortcuts that aren't globally applicable, causing cognitive overload.
**Action:** When designing shortcut hint bars, dynamically render hints based on the active pane (e.g., input vs output) and state (e.g., empty vs populated input) rather than listing all possible shortcuts statically.
