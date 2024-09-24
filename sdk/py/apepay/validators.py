from typing import TYPE_CHECKING, Any

from ape.contracts.base import ContractInstance
from ape.exceptions import ContractLogicError
from ape.types import AddressType
from ape.utils import BaseInterfaceModel
from eth_utils import to_int
from pydantic import field_validator

from .package import MANIFEST

if TYPE_CHECKING:
    from .manager import StreamManager


class Validator(BaseInterfaceModel):
    """
    Wrapper class around a Validator contract that is connected with a specific
    `stream_manager` on chain.
    """

    address: AddressType
    manager: "StreamManager"

    def __init__(self, address: str | AddressType, /, *args, **kwargs):
        kwargs["address"] = address
        super().__init__(*args, **kwargs)

    @field_validator("address", mode="before")
    def normalize_address(cls, value: Any) -> AddressType:
        if isinstance(value, Validator):
            return value.address

        return cls.conversion_manager.convert(value, AddressType)

    @property
    def contract(self) -> ContractInstance:
        return self.chain_manager.contracts.instance_at(
            self.address,
            contract_type=MANIFEST.Validator.contract_type,
        )

    def __hash__(self) -> int:
        # NOTE: So `set` works
        return self.address.__hash__()

    def __gt__(self, other: Any) -> bool:
        # NOTE: So `sorted` works
        if isinstance(other, (Validator, ContractInstance)):
            return to_int(hexstr=self.address.lower()) > to_int(hexstr=other.address.lower())

        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, (Validator, ContractInstance)):
            return self.address == other.address

        # Try __eq__ from the other side.
        return NotImplemented

    def __call__(self, *args, **kwargs) -> bool:
        try:
            # NOTE: Imitate that the call is coming from the specified StreamManager.
            #       Also note that a validator can be connected to >1 StreamManagers.
            self.contract._mutable_methods_["validate"].call(
                *args, sender=self.manager.address, **kwargs
            )
            return True

        except ContractLogicError:
            return False