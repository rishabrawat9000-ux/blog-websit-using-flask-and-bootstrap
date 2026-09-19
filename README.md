# Thought Trail

A small Flask blog ready for a WSGI host such as Render, Railway, Fly.io, or Heroku. It uses SQLite locally and PostgreSQL when `DATABASE_URL` is provided.

## Run locally

Create and activate a virtual environment, then install the production dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to a private `.env` file and use its commands to generate a `SECRET_KEY` and `ADMIN_PASSWORD_HASH`. Export those values in your shell (or configure them in your IDE), then run:

```bash
flask --app app run --debug
```

The local SQLite database is created automatically in `instance/blog.db`.

## Deploy

1. Push this folder to a Git repository. Never commit `.env` or real credentials.
2. Create a web service from the repository. `render.yaml` provides a Render blueprint; other WSGI platforms can use the included `Procfile`.
3. Set `SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD_HASH` in the host's encrypted environment-variable settings. Generate the password hash with the command in `.env.example`.
4. Attach PostgreSQL and set its connection string as `DATABASE_URL`. The app accepts both `postgres://` and `postgresql://` URLs.
5. Set `FLASK_ENV=production` and deploy. The host starts `gunicorn --workers 2 --bind 0.0.0.0:$PORT app:app`.

## Uploads

The built-in upload folder is suitable for local development. Most hosts use ephemeral disk storage, so uploaded images can disappear after a redeploy. Before relying on uploads in production, configure a persistent volume through `UPLOAD_FOLDER` or switch uploads to object storage (for example, S3 or Cloudinary).
