"""LangGraph orchestration: a stateful tool-calling agent loop with persistent memory.

State is just the running message list (LangGraph's built-in MessagesState). The model node calls
ChatGoogleGenerativeAI bound to the six tools in tools.py; if it emits tool calls, `tools_condition` routes
to the tool node, which executes them and loops back to the model; once the model answers without calling
a tool, the graph ends - the standard ReAct tool-use loop, built explicitly here (rather than via
LangGraph's one-line prebuilt agent helper) so the state schema, nodes, and routing are all visible and
easy to extend.

"Remember previous conversations" is not a tool or an app-level database table here - it's the
checkpointer. Every invocation is scoped to a thread_id, and the checkpointer persists the full message
state for that thread between HTTP requests, so the next call with the same thread_id resumes exactly
where the conversation left off. This demo uses a local SQLite checkpointer (genuinely persistent, no
server required); swapping to `langgraph-checkpoint-postgres`'s PostgresSaver for a multi-instance
production deployment is a one-line change since every checkpointer implements the same interface.
"""
import sqlite3
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from app.core.config import get_settings
from app.services.assistant.tools import ALL_TOOLS

CHECKPOINT_PATH = Path(__file__).resolve().parent / "storage" / "checkpoints.sqlite3"

SYSTEM_PROMPT = """You are the AI shopping assistant for Pricewise. You can search the product catalog and \
buyer reviews, look up full specifications, compare products, find alternatives, recommend products based \
on stated needs, and search the live web for anything beyond Pricewise's own catalog - always by calling \
the appropriate tool rather than answering from memory.

Rules:
- Never state a price, rating, or specification you have not just retrieved via a tool call in this conversation.
- When comparing products or explaining specifications, call get_product_details or compare_products to get \
exact figures rather than paraphrasing a search snippet.
- Always also call web_search to supplement or verify catalog answers with live information - general \
product knowledge, comparisons to products Pricewise doesn't stock, recent news - rather than treating it \
only as a fallback for when the catalog has nothing.
- Clearly distinguish Pricewise catalog/review facts from web_search results when you cite them.
- Always state prices in INR (₹), never any other currency symbol or code. Catalog tool results are already \
converted to INR for you. A web_search result that quotes a price in another currency (e.g. USD, EUR) must \
be converted to an approximate INR figure before you state it - never repeat the original currency as-is.
- If a tool returns no results or an error, say so plainly rather than guessing.
- Be concise, and use the shopper's stated budget or preferences to narrow recommendations rather than listing everything.
- Write in plain prose - no markdown headers (#), no bullet or numbered lists. The only markdown you may \
use is **double asterisks** around the single most important piece of information in a response (a product \
name, price, or the one key spec that answers the question), so it stands out at a glance. Bold sparingly: \
never a whole sentence, and skip it entirely if nothing is more important than the rest."""


def _default_model_node(state: MessagesState) -> dict:
    settings = get_settings()
    model = ChatGoogleGenerativeAI(model=settings.assistant_chat_model, api_key=settings.gemini_api_key, temperature=0).bind_tools(ALL_TOOLS)
    response = model.invoke([SystemMessage(content=SYSTEM_PROMPT), *state["messages"]])
    return {"messages": [response]}


def build_graph(model_node: Callable[[MessagesState], dict] | None = None) -> CompiledStateGraph:
    """`model_node` is overridable so tests can substitute a scripted fake model without needing a real API key."""
    builder = StateGraph(MessagesState)
    builder.add_node("model", model_node or _default_model_node)
    builder.add_node("tools", ToolNode(ALL_TOOLS))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition)
    builder.add_edge("tools", "model")

    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(CHECKPOINT_PATH), check_same_thread=False)
    checkpointer = SqliteSaver(connection)
    return builder.compile(checkpointer=checkpointer)


@lru_cache
def get_graph() -> CompiledStateGraph:
    """Build once per process - the SQLite connection and compiled graph are reused across requests."""
    return build_graph()
