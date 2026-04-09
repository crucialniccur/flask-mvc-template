# 🔐 Flask MVC Setup — Step 2 (.env, Neon PostgreSQL, Cloudinary Image Upload)

> **Prerequisites:** Step 1 must be complete and working before starting Step 2.
> This section covers moving secrets out of your code, switching from SQLite to a
> hosted PostgreSQL database on Neon, and integrating Cloudinary for image uploads.

---

## 📖 Table of Contents

1. [What Changes in Step 2?](#what-changes)
2. [New Project Structure](#project-structure)
3. [Part 1 — The `.env` File](#part-1-env)
4. [Part 2 — Neon PostgreSQL](#part-2-neon)
5. [Part 3 — Cloudinary Image Upload](#part-3-cloudinary)
6. [Updated Files — Full Code](#updated-files)
7. [Run Sequence](#run-sequence)
8. [Testing in Postman](#testing)
9. [⚠️ Cautions & Gotchas](#cautions)
10. [Key Concepts Explained](#key-concepts)

---

## 1. What Changes in Step 2? <a name="what-changes"></a>

|               | Step 1                   | Step 2                                            |
| ------------- | ------------------------ | ------------------------------------------------- |
| Database      | SQLite (local file)      | Neon PostgreSQL (hosted)                          |
| Secrets       | Hardcoded in `config.py` | In `.env` file                                    |
| Image storage | None                     | Cloudinary (external API)                         |
| New folders   | —                        | `utils/`                                          |
| New files     | —                        | `.env`, `.flaskenv`, `utils/cloudinary_helper.py` |

---

## 2. New Project Structure <a name="project-structure"></a>

```
your-project/
├── .env                            ← ⚠️ NEVER commit this — secrets live here
├── .gitignore                      ← must include .env
├── Pipfile
├── Pipfile.lock
├── README.md
└── server/
    ├── .flaskenv                   ← Flask CLI variables (safe to commit)
    ├── app.py
    ├── config.py                   ← reads from .env via load_dotenv()
    ├── seed.py
    ├── migrations/
    ├── models/
    │   ├── __init__.py
    │   └── user.py                 ← added image_url column
    ├── controllers/
    │   ├── __init__.py
    │   └── user_controller.py      ← added POST with image upload
    └── utils/                      ← new — shared helper functions
        ├── __init__.py
        └── cloudinary_helper.py    ← Cloudinary upload logic
```

---

## 3. Part 1 — The `.env` File <a name="part-1-env"></a>

### Why `.env`?

If you hardcode secrets directly in `config.py`:

```python
# ❌ Never do this
class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://user:mypassword@host/db"
    CLOUDINARY_API_SECRET = "abc123supersecret"
```

The moment you push to GitHub, **everyone can see your database password and API keys**.
People run bots that scan GitHub for exposed credentials 24/7. Your database will be
compromised within minutes.

A `.env` file keeps secrets local — it never gets pushed to GitHub.

### Create `.env` at the project root

```bash
# .env  ← lives at project root, same level as Pipfile
DATABASE_URL="postgresql://username:password@host/dbname?sslmode=require&channel_binding=require"
CLOUDINARY_CLOUD_NAME="your_cloud_name"
CLOUDINARY_API_KEY="your_api_key"
CLOUDINARY_API_SECRET="your_api_secret"
```

> ⚠️ **CAUTION 1 — Always wrap values in double quotes**
>
> The `&` character in your database URL means "run in background" in shell.
> Without quotes, everything after `&` gets cut off silently:
>
> ```bash
> # ❌ Shell cuts off at & — channel_binding becomes "re" → connection fails
> DATABASE_URL=postgresql://host/db?sslmode=require&channel_binding=require
>
> # ✅ Quotes tell shell: this whole thing is one value
> DATABASE_URL="postgresql://host/db?sslmode=require&channel_binding=require"
> ```

### Confirm `.env` is in `.gitignore`

```zsh
# Check
cat .gitignore | grep .env

# If not there, add it
echo ".env" >> .gitignore
```

### Create `.flaskenv` inside `server/`

This file is for Flask CLI variables only — no secrets. It IS safe to commit.

```bash
# server/.flaskenv
FLASK_APP=app.py
FLASK_RUN_PORT=5555
FLASK_DEBUG=True
```

With this file, you no longer need to run `export FLASK_APP=app.py` every session.
Flask reads `.flaskenv` automatically.

---

## 4. Part 2 — Neon PostgreSQL <a name="part-2-neon"></a>

### Setting up Neon

1. Go to [neon.tech](https://neon.tech) and create a free account
2. Create a new project
3. Create a database

> ⚠️ **CAUTION 2 — Do NOT enable Neon Auth when creating your database**
>
> Neon Auth is a managed authentication service that automatically adds its own
> tables to your database. Leave it disabled until you know what it does.
> Enabling it will add unexpected tables that will confuse your migrations.

4. Go to your project dashboard → Connection Details
5. Copy the connection string — it looks like:
   ```
   postgresql://neondb_owner:password@ep-something.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```

> ⚠️ **CAUTION 3 — Copy the raw URL, not the psql command**
>
> Neon sometimes shows you a `psql` command like this:
>
> ```bash
> psql 'postgresql://neondb_owner:password@host/neondb?sslmode=require'
> ```
>
> You want ONLY the URL inside the quotes — not the word `psql`, not the outer quotes:
>
> ```bash
> # ✅ What goes in .env
> DATABASE_URL="postgresql://neondb_owner:password@host/neondb?sslmode=require&channel_binding=require"
> ```

### Verify the connection

```zsh
# From inside server/ with venv active
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.environ.get('DATABASE_URL'))"
```

You should see the full URL printed — including `channel_binding=require` at the end.
If it's cut off or shows `None`, re-check your `.env` file.

---

## 5. Part 3 — Cloudinary Image Upload <a name="part-3-cloudinary"></a>

### Why Cloudinary?

You cannot store image files in a PostgreSQL database (well, technically you can,
but you really shouldn't). Instead you store the image on Cloudinary's servers
and save the **URL** in your database.

```
User uploads image
       ↓
Flask receives the file
       ↓
Flask sends file to Cloudinary API
       ↓
Cloudinary stores it and returns a URL
       ↓
Flask saves that URL in the users table
       ↓
Client gets back { "image_url": "https://res.cloudinary.com/..." }
```

### Setup

1. Create a free account at [cloudinary.com](https://cloudinary.com)
2. Go to Dashboard → copy your Cloud Name, API Key, and API Secret
3. Add them to `.env`

Install the package:

```zsh
pipenv install cloudinary
```

### Why `form-data` and not JSON for image uploads?

JSON is text. An image is binary data — bytes representing pixels. You cannot
cleanly put binary data inside a JSON string:

```json
// ❌ This doesn't work
{
    "name": "Alice",
    "image": "�PNG\r\n..."   ← binary gibberish, JSON can't handle this
}
```

`multipart/form-data` is specifically designed to carry **mixed content** — both
text fields AND binary files in the same request. That's why in the controller
we read from two different places:

```python
name = request.form.get("name")    # ← text comes from form
file = request.files.get("image")  # ← file comes from files
```

> 💡 **Rule of thumb:**
>
> - Request includes a file → use `form-data` + `request.form` / `request.files`
> - Request is pure text/numbers → use `application/json` + `request.get_json()`

---

## 6. Updated Files — Full Code <a name="updated-files"></a>

### `server/config.py`

```python
# server/config.py
import os

from dotenv import load_dotenv

load_dotenv()  # ← reads .env and loads into os.environ — must be CALLED, not just imported


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_COMPACT = False
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")
```

> ⚠️ **CAUTION 4 — Import is not the same as calling**
>
> This is a very easy mistake:
>
> ```python
> # ❌ Imported but never called — .env never loads — all values are None
> from dotenv import load_dotenv  # noqa: F401
>
> # ✅ Imported AND called — .env is loaded
> from dotenv import load_dotenv
> load_dotenv()
> ```
>
> If Ruff adds `# noqa: F401` to your `load_dotenv` import, it means you forgot
> to call it. Ruff saw an unused import and flagged it. Remove the noqa comment
> and add the `load_dotenv()` call.

---

### `server/models/user.py`

```python
# server/models/user.py
from sqlalchemy_serializer import SerializerMixin

from . import db


class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String, nullable=True)  # ← new column

    def __repr__(self):
        return f"<User {self.name}>"
```

---

### `server/utils/__init__.py`

```python
# server/utils/__init__.py
# empty — marks utils/ as a Python package
```

---

### `server/utils/cloudinary_helper.py`

```python
# server/utils/cloudinary_helper.py
import cloudinary
import cloudinary.uploader
from flask import current_app


def configure_cloudinary():
    cloudinary.config(
        cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=current_app.config["CLOUDINARY_API_KEY"],
        api_secret=current_app.config["CLOUDINARY_API_SECRET"],
    )


def upload_image(file):
    configure_cloudinary()
    result = cloudinary.uploader.upload(file)
    return result["secure_url"]  # ← returns the hosted image URL string
```

> 💡 `current_app` is Flask's way of accessing the app instance from outside
> `app.py`. It works because we're inside a request context when this runs.

---

### `server/controllers/user_controller.py`

```python
# server/controllers/user_controller.py
from flask import Blueprint, request
from flask_restful import Api, Resource

from models import db
from models.user import User as UserModel  # ← aliased to avoid name collision
from utils.cloudinary_helper import upload_image

user_bp = Blueprint("users", __name__, url_prefix="/users")
api = Api(user_bp)


class UserList(Resource):
    def get(self):
        users = [u.to_dict() for u in UserModel.query.all()]
        return users, 200

    def post(self):
        name = request.form.get("name")   # ← form-data, not JSON
        file = request.files.get("image") # ← binary file from form-data

        if not name:
            return {"error": "name is required"}, 400

        image_url = None
        if file:
            image_url = upload_image(file)  # sends to Cloudinary, returns URL

        user = UserModel(name=name, image_url=image_url)
        db.session.add(user)
        db.session.commit()

        return user.to_dict(), 201


class UserByID(Resource):
    def get(self, id):
        user = UserModel.query.get(id)  # ← UserModel not User (name collision!)
        if not user:
            return {"error": "user not found."}, 404
        return user.to_dict(), 200


api.add_resource(UserList, "/")
api.add_resource(UserByID, "/<int:id>")
```

> ⚠️ **CAUTION 5 — The name collision in controllers (reminder from Step 1)**
>
> You import your SQLAlchemy model AND define a Resource class. If both are named
> `User`, the class definition overwrites the import:
>
> ```python
> from models.user import User       # ← first User
> class User(Resource):              # ← second User kills the first
>     def get(self, id):
>         User.query.get(id)         # ← AttributeError: Resource has no .query
> ```
>
> Two fixes:
>
> ```python
> # Fix A — alias the import (used above)
> from models.user import User as UserModel
>
> # Fix B — rename the Resource class
> class UserList(Resource): ...
> class UserByID(Resource): ...
> ```

---

### `server/app.py`

```python
# server/app.py
from config import Config
from controllers.user_controller import user_bp
from flask import Flask
from flask_migrate import Migrate
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        from models import user  # noqa: F401

    app.register_blueprint(user_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5555, debug=True)
```

---

### `server/seed.py`

```python
# server/seed.py
from app import app
from models import db
from models.user import User

with app.app_context():
    print("Clearing old data since it is still dev mode not production mode.....")
    User.query.delete()

    print("Seeding users.....")
    users = [
        User(name="Alice", image_url=None),
        User(name="Bob", image_url=None),
        User(name="Charlie", image_url=None),
    ]

    db.session.add_all(users)
    db.session.commit()
    print("Done! ✅")
```

---

## 7. Run Sequence <a name="run-sequence"></a>

### First time setup for Step 2

```zsh
# 1. From project root — install new dependency
pipenv install cloudinary

# 2. Enter venv
pipenv shell

# 3. Go into server/
cd server

# 4. Apply migrations to Neon (new column was added)
flask db migrate -m "add image_url column to users table"
flask db upgrade

# 5. Seed the database
python seed.py

# 6. Start the server
flask run
```

### If you hit "Target database is not up to date"

This means your Neon database has migrations that haven't been applied yet.
Always run `upgrade` before `migrate`:

```zsh
flask db upgrade      # apply existing migrations first
flask db migrate -m "your message"   # then generate new ones
flask db upgrade      # apply the new one
```

---

## 8. Testing in Postman <a name="testing"></a>

| Method | URL                             | Body Type     | Fields                         |
| ------ | ------------------------------- | ------------- | ------------------------------ |
| GET    | `http://localhost:5555/users/`  | none          | —                              |
| GET    | `http://localhost:5555/users/1` | none          | —                              |
| POST   | `http://localhost:5555/users/`  | **form-data** | `name` (Text) + `image` (File) |

> ⚠️ For the POST request — in Postman set Body to **form-data**, NOT raw JSON.
> Under the `image` key, change the type dropdown from Text to **File** and
> select an image from your computer.

Expected POST response:

```json
{
  "id": 4,
  "name": "Diana",
  "image_url": "https://res.cloudinary.com/yourcloud/image/upload/v123/abc.jpg"
}
```

---

## 9. ⚠️ Cautions & Gotchas <a name="cautions"></a>

### C1 — Wrap `.env` values in double quotes

```bash
# ❌ & cuts off the URL — channel_binding becomes "re" → connection fails
DATABASE_URL=postgresql://host/db?sslmode=require&channel_binding=require

# ✅
DATABASE_URL="postgresql://host/db?sslmode=require&channel_binding=require"
```

### C2 — Do not enable Neon Auth

When creating a Neon database, leave **Neon Auth** disabled. It adds managed
auth tables to your database automatically — not what you want at this stage.

### C3 — Remove `psql` from the connection string

Neon shows a `psql` command. You only want the raw URL:

```bash
# ❌ This is a shell command, not a URL
psql 'postgresql://user:pass@host/db?sslmode=require'

# ✅ Raw URL only, wrapped in quotes
DATABASE_URL="postgresql://user:pass@host/db?sslmode=require&channel_binding=require"
```

### C4 — `load_dotenv` must be called, not just imported

```python
# ❌ Imported but never called — .env never loads
from dotenv import load_dotenv  # noqa: F401

# ✅ Called immediately after import
from dotenv import load_dotenv
load_dotenv()
```

### C5 — Name collision: model vs Resource class (reminder)

```python
# ❌ Class definition overwrites the import
from models.user import User
class User(Resource): ...

# ✅ Alias the import
from models.user import User as UserModel
class UserList(Resource): ...
```

### C6 — POST with image must use form-data not JSON

```python
# ❌ Files cannot be sent as JSON
data = request.get_json()

# ✅ Files come through form-data
name = request.form.get("name")
file = request.files.get("image")
```

### C7 — "Target database is not up to date"

```zsh
# Run upgrade first, then migrate
flask db upgrade
flask db migrate -m "your message"
flask db upgrade
```

---

## 10. Key Concepts Explained <a name="key-concepts"></a>

### What does `load_dotenv()` do?

It reads the `.env` file and loads each key-value pair into `os.environ` — the
same place environment variables live. After calling it, `os.environ.get("DATABASE_URL")`
works as if you had typed `export DATABASE_URL=...` in your terminal.

### Why does `DATABASE_URL` need quotes in `.env`?

The `&` character means "run in background" in shell. Without quotes, your URL
gets split at `&` and only the first part is assigned. Wrapping in double quotes
tells the shell to treat the entire string as one value.

### Why alias `User as UserModel`?

In a controller file you import your SQLAlchemy model (`User`) AND define a
Flask-RESTful Resource class. If both are named `User`, Python uses the most
recently defined one — your Resource class. The model import is silently lost.
Aliasing as `UserModel` gives each thing a unique name.

### Why `form-data` instead of `request.get_json()` for image uploads?

JSON is a text format. Images are binary data — raw bytes. Binary data cannot
be cleanly represented inside a JSON string. `multipart/form-data` is the HTTP
standard for sending mixed content (text + binary files) in a single request.
That's why text fields come from `request.form` and files come from
`request.files` — they travel in different parts of the same request.

---
