1. Run `.start.sh`
2a. Change the `settings.json` in faker and the `.env.development` to your local database
2b. Dont change the `env.testing` and change the `DJANGO_ENV` in `.env` to testing to use the supabase database "for testing"
3. For testing and development run `tailwind_watch.sh` for dynamic style building
4. Run `py manage runserver` to start the application