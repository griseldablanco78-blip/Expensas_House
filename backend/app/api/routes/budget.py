"""Budget HTTP routes."""
from fastapi import APIRouter, HTTPException
from backend.app.api.schemas import BudgetModel, ExpenseModel
from backend.app.infrastructure.json_store import get_user_prefs, update_user_prefs, get_expenses, add_expense

router = APIRouter(tags=["budget"])


@router.get("/api/budget")
def api_get_budget(month: str | None = None):
    """Retorna el presupuesto mensual y el total gastado."""
    if month is not None:
        from backend.app.services.expense_reporting import monthly_summary
        try:
            return monthly_summary(month)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
    return get_user_prefs()



@router.post("/api/budget")
def api_set_budget(budget: BudgetModel):
    """Establece el monto de presupuesto mensual."""
    res = update_user_prefs({"monthlyBudget": budget.monthlyBudget})
    return {"status": "success", "user_prefs": res}



@router.get("/api/expenses")
def api_get_expenses():
    """Retorna el historial de gastos registrados."""
    return get_expenses()



@router.post("/api/expenses")
def api_add_expense(expense: ExpenseModel):
    """Registra un nuevo gasto / ticket de compra."""
    saved = add_expense(expense.model_dump())
    return {"status": "success", "expense": saved}
