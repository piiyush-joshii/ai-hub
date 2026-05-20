from pydantic import BaseModel


class ContractValidationRequest(BaseModel):
    request_id: str
    contract_text: str
    contract_filename: str
