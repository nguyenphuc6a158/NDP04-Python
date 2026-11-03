import logging
from threading import Thread

from fastapi import FastAPI
from dotenv import load_dotenv

from app.container import Settings, build_voice_handler
from app.interfaces.ws.device_socket import router as device_router

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings or Settings.from_environment()
    application = FastAPI(
        title="NDP04",
        description="Robot AI NDP04",
        version="0.1.0",
    )
    application.state.voice_handler = build_voice_handler(configuration)
    application.state.device_api_token = configuration.device_api_token
    application.include_router(device_router)

    @application.get("/")
    def root() -> dict[str, str]:
        return {"project": "NDP04", "status": "running"}

    @application.get("/get/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
Thread(target=app.state.voice_handler.warm_up, daemon=True).start()