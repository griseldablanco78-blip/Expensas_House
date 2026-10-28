"""HTTP request contracts shared by the API routes."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class StockItemModel(BaseModel):
    id: Optional[str] = None
    name: str
    brand: Optional[str] = "Genérica"
    category: str
    stockQuantity: int = 1
    inUseCount: int = 0
    unit: Optional[str] = "unidad"
    price: Optional[float] = 0.0



class ShoppingItemModel(BaseModel):
    id: Optional[str] = None
    name: str
    brand: Optional[str] = "Genérica"
    category: str
    detail: Optional[str] = "Agregado manual"
    quantity: int = 1
    suggestedStore: Optional[str] = None
    checked: bool = False



class BudgetModel(BaseModel):
    monthlyBudget: float



class ExpenseModel(BaseModel):
    id: Optional[str] = None
    category: str
    amount: float = Field(gt=0, allow_inf_nan=False)
    timestamp: Optional[int] = None
    note: Optional[str] = ""



class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None



class AndroidSyncPayload(BaseModel):
    baseline: Optional[Dict[str, Any]] = None
    stock: Optional[List[Dict[str, Any]]] = None
    shopping: Optional[List[Dict[str, Any]]] = None
    expenses: Optional[List[Dict[str, Any]]] = None
    user_prefs: Optional[Dict[str, Any]] = None
    offers: Optional[List[Dict[str, Any]]] = None



class ReceiptLine(BaseModel):
    description: str = Field(min_length=1, max_length=250)
    quantity: float = Field(gt=0, allow_inf_nan=False)
    unit_price: float = Field(gt=0, allow_inf_nan=False)
    line_total: float = Field(gt=0, allow_inf_nan=False)



class ReceiptCommit(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    store: str = Field(min_length=1, max_length=150)
    items: List[ReceiptLine] = Field(min_length=1, max_length=300)
    total: float = Field(gt=0, allow_inf_nan=False)
    category: str = "Comestibles"
    adjustment_note: str = ""



class ReceiptText(BaseModel):
    text: str = Field(max_length=100000)
