import os
from typing import Literal, Optional

from load_dotenv import load_dotenv
from pydantic import BaseModel, Field

DataProvider = Literal['data-exchange-api', 'dummy']


class Configuration(BaseModel):
    debug_mode: bool = Field(default=False,
                             description="Use random data instead of connecting to the data exchange server")

    listen_address: str = Field(default="0.0.0.0",
                                description="Address on which the dashboard web-server should listen")
    listen_port: int = Field(default=8080,
                             ge=0,
                             le=65535,
                             description="Port on which the dashboard web-server should listen")

    data_provider: DataProvider = Field(default='data-exchange-api',
                                        description='TODO')

    data_exchange_endpoint: Optional[str] = Field(
        default=None,
        description="REST endpoint for the INDICATE data exchange server"
    )


def load_configuration(config_file: str = ".env") -> Configuration:
    """
    Loads the configuration from a file or environment variables.
    Environment variables take precedence over values in the configuration file.
    """
    load_dotenv(config_file)

    provider_id = os.getenv("PROVIDER_ID")
    if provider_id is None:
        provider_id_file = os.getenv("PROVIDER_ID_FILE")
        if provider_id_file is not None:
            with open(provider_id_file) as file:
                provider_id = file.read().strip()

    from_environment = {
        "listen_address":         os.getenv("LISTEN_ADDRESS"),
        "listen_port":            os.getenv("LISTEN_PORT"),
        "data_provider":          os.getenv("DATA_PROVIDER"),
        "data_exchange_endpoint": os.getenv("DATA_EXCHANGE_ENDPOINT"),
        "provider_id":            provider_id,
    }
    args = {k: v for k, v in from_environment.items() if v is not None}
    return Configuration(**args)
