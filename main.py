import uvicorn

from conf.config import settings

if __name__ == '__main__':
    uvicorn.run(
        app="api.app:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT
    )