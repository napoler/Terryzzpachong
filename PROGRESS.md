# Progress

## Completed

*   **Project Setup:**
    *   Set up the Python project structure.
    *   Configured dependencies (`libtorrent`, `PySide6`).
*   **Core Functionality:**
    *   Implemented a functional DHT crawler using `libtorrent`.
    *   Created the SQLite database for storing torrent metadata (name, size, files, info-hash).
    *   Implemented a 5-second delayed start for the crawler to ensure a smooth launch.
*   **User Interface (PySide6/Qt):**
    *   Switched the UI from `tkinter` to `PySide6` for a more professional look and feel.
    *   Redesigned the main window to mimic the qBittorrent layout.
    *   Added a main menu bar and a placeholder settings page.
    *   Implemented a right-click context menu for "Find Related Seeds".
*   **Documentation:**
    *   Created initial project documentation (`README.md`, `DEVELOPMENT.md`, etc.).
    *   Updated all documentation to reflect the current state of the project.

## Planned

*   **Enhanced Discovery:**
    *   Add support for crawling public trackers and using the Peer Exchange Protocol (PEX).
*   **GUI Improvements:**
    *   Implement advanced filtering in the sidebar (by type, size, etc.).
    *   Add a bottom panel to show detailed information for the selected torrent (e.g., file list).
*   **Testing:**
    *   Develop a comprehensive test suite to ensure application stability and correctness.
