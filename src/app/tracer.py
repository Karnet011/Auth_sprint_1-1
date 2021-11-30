from jaeger_client import Config
from app.settings import settings


def setup_jaeger():
    jaeger_config = {
        "sampler": {
            "type": settings.JAEGER.JAEGER_TYPE,
            "param": 1,
        },
        "local_agent": {
            "reporting_host": settings.JAEGER.REPORTING_HOST,
            "reporting_port": settings.JAEGER.REPORTING_PORT,
        },
        "logging": True,
    }
    config = Config(
        config=jaeger_config,
        service_name=settings.JAEGER.SERVICE_NAME,
        validate=True,
    )
    return config.initialize_tracer()
