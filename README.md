## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### 1. Initial Setup

```bash
./start.sh
```

This script installs dependencies and prepares the project environment.

---

### 2. Configure Environment

* Update the following files to match your **local database**:

  * `faker/settings.json`
  * `.env.development`

* ⚠️ Do **not** modify:

  * `.env.testing`

* To use the **Supabase testing database**:

  * Open `.env`
  * Set:

    ```env
    DJANGO_ENV=testing
    ```

---

### 3. Run Tailwind (for styling)

For development and testing, start Tailwind in watch mode:

```bash
./tailwind_watch.sh
```

This ensures styles are rebuilt automatically as you work.

---

### 4. Start the Development Server

```bash
python manage.py runserver
```

Your app should now be running locally 🚀

---

### 🧠 Notes

* Use **development environment** for local DB work
* Use **testing environment** for shared Supabase DB
* Tailwind watcher must be running for styles to update in real-time

