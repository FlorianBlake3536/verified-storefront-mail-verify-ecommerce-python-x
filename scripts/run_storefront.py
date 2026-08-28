import os

import uvicorn


if __name__ == "__main__":
    os.environ.setdefault("PUBLIC_BASE_URL", "http://localhost:8000")
    uvicorn.run("storefront_mail.service:app", host="127.0.0.1", port=8000)

