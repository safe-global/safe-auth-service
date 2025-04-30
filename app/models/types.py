from pydantic import Field, SecretStr

from typing_extensions import Annotated

passwordType = Annotated[SecretStr, Field(min_length=8)]
