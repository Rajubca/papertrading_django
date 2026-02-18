This is in Django and provide facility to workin live market paper trading
python -m daphne -p 8000 papertrading.asgi:application

## SPA & UI Transformation

This project has been transformed into a Single Page Application (SPA) using **HTMX** and **Bootstrap 5**.

### Key Features
*   **India Professional Theme**: A modern color palette featuring Deep Navy Blue (#002D62), Saffron (#FF9933), and Green (#138808).
*   **Seamless Navigation**: Uses HTMX to swap content in the main dashboard without full page reloads.
*   **Dynamic Modals**: "Create Portfolio" and "Trade Stock" actions open in Bootstrap modals loaded dynamically via HTMX.
*   **Mobile Optimized**: Responsive tables and layouts for better mobile experience.

### Technical Details
*   **Partials**: Views now return partial HTML fragments (located in `trading/templates/trading/partials/`) for HTMX requests, falling back to full pages for direct access.
*   **HTMX Integration**:
    *   `hx-target="#main-content"`: Updates only the main content area.
    *   `hx-push-url="true"`: Updates the browser URL for history navigation.
    *   `hx-swap="innerHTML swap:200ms"`: Provides smooth fade transitions.
*   **Global Loader**: A spinner indicator shows during HTMX requests.

### Usage
Run the server as usual:
```bash
python -m daphne -p 8000 papertrading.asgi:application
```
