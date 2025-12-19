# chatbot_core.py

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, TypedDict

from chromadb.config import Settings
from langchain_chroma import Chroma

from models import build_llm, build_embedding_model, HFChatModel


CHROMA_DB_DIR = "./chroma_db"
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")


# ====================== State definition ====================== #

class ConversationState(TypedDict):
    messages: List[Dict[str, Any]]
    user_input_reph: str
    knowledge_snippets: str
    metadata: Dict[str, Any]
    memory_summary: str


# ====================== Prompts ====================== #

REPHRASE_PROMPT = """You are a helpful assistant that rewrites user questions for retrieval.

Conversation so far:
{chat_history}

User question:
{user_input}

Rewrite the user question as a single, clear, standalone query.
- Keep the same meaning.
- Do NOT answer the question.
- Make it understandable without any additional context.
- IF the user question is semantically unrelated to the previous parts of the conversation, do not
integrate it with the memory. (Example: previous question = "i lost my password", next question = "where do i see
my bank account statement?", in this case the context should play a very little role in the rephrasing)
- If the user input is not a real question, or the material is too little/noisy for an acceptable rephrasing, you
should instruct the answer generation model to ask the user for clarity or additional context.
"""

ANSWER_PROMPT = """You are a helpful support assistant for a fintech company website.
You have to help the user with whatever problem they might be facing.
Remember to be nice, but not too formal.

You will answer the user's question based ONLY on the provided knowledge snippets.
If the answer is not in the snippets, say you don't know and suggest looking for help on the company website, 
especially on the FAQ section.
Never mention explicitly the knowledge base, the snippets, or anything like that.

Conversation summary (may be empty):
{memory_summary}
NB: remember that the memory that you use to answer should be coherent with the last user question,
which is the most important piece of information!

Knowledge snippets:
{knowledge_snippets}

User question:
{question}

Now provide a concise, helpful, and accurate answer grounded in the knowledge snippets.
If you don't know, explicitly say so.
If the user question does not contain a real question, or it is something completely unrelated
to your scope, ask them to try and rephrase their question.
"""

MEMORY_SUMMARY_PROMPT = """You are a summarization assistant.

Existing conversation summary (may be empty):
{existing_summary}

New conversation turns:
{history}

Update and return a concise summary (3–5 sentences) that captures:
- the user's main goals or issues
- any important decisions or constraints
- key facts that might be relevant later

Do NOT invent information.
"""


# ====================== Vector store attach ====================== #a

def attach_vector_store() -> Chroma:
    """
    Attach to existing Chroma collection created by index_kb.py.

    We still need an embedding function to embed queries consistently.
    """
    embedding_model = build_embedding_model()
    settings = Settings(anonymized_telemetry=False)

    vector_store = Chroma(
        collection_name="demo_kb",
        embedding_function=embedding_model,
        persist_directory=CHROMA_DB_DIR,
        client_settings=settings,
    )
    return vector_store


# ====================== Memory helpers ====================== #

def build_chat_history(messages: List[Dict[str, Any]], max_turns: int = 4) -> str:
    if len(messages) <= 1:
        return "No prior conversation."

    # last max_turns messages excluding the very last user question
    history_messages = messages[-(max_turns + 1):-1]
    if not history_messages:
        return "No prior conversation."

    lines: List[str] = []
    for m in history_messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        lines.append(f"{role}: {content}")

    return "\n".join(lines)


def update_memory_summary(
    state: ConversationState,
    llm: HFChatModel,
    max_history_turns: int = 6,
) -> ConversationState:
    messages = state["messages"]
    if len(messages) <= max_history_turns:
        return state

    to_summarize = messages[:-max_history_turns]
    if not to_summarize:
        return state

    existing_summary = state.get("memory_summary", "")

    history_text = "\n".join(
        f'{m.get("role", "user")}: {m.get("content", "")}'
        for m in to_summarize
    )

    prompt = MEMORY_SUMMARY_PROMPT.format(
        existing_summary=existing_summary,
        history=history_text,
    )

    summary = llm.invoke(prompt)
    state["memory_summary"] = str(summary).strip()
    return state


# ====================== Nodes ====================== #

def rephrase_node(state: ConversationState, llm: HFChatModel) -> ConversationState:
    latest_user_msg = state["messages"][-1]["content"]
    chat_history = build_chat_history(state["messages"])

    prompt = REPHRASE_PROMPT.format(
        chat_history=chat_history,
        user_input=latest_user_msg,
    )

    rephrased = llm.invoke(prompt)
    state["user_input_reph"] = str(rephrased).strip()
    return state


def retrieval_node(state: ConversationState, vector_store: Chroma, top_k: int = 3) -> ConversationState:
    query = state["user_input_reph"]
    metadata = state["metadata"]

    desired_client_type = metadata.get("client_type")
    chroma_filter: Dict[str, Any] = {}
    if desired_client_type:
        chroma_filter["client_type"] = desired_client_type

    # Retrieve docs + scores
    if chroma_filter:
        docs_and_scores = vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=chroma_filter,
        )
    else:
        docs_and_scores = vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
        )

    # Filter by distance (lower distance = better match)
    filtered_docs = []
    for doc, distance in docs_and_scores:
        if distance is None:
            continue
        if distance <= max_distance:
            filtered_docs.append(doc)

    snippets: List[str] = []
    for doc in filtered_docs:
        doc_id = doc.metadata.get("id", "unknown-id")
        category = doc.metadata.get("category", "unknown-category")
        client_type = doc.metadata.get("client_type", "unknown-client-type")
        header = f"[{doc_id} | {category} | {client_type}]"
        snippets.append(f"{header}\n{doc.page_content}")

    state["knowledge_snippets"] = "\n\n---\n\n".join(snippets) if snippets else ""
    return state


def answer_node(state: ConversationState, llm: HFChatModel) -> ConversationState:
    question = state["messages"][-1]["content"]
    chat_history = build_chat_history(state["messages"])
    memory_summary = state.get("memory_summary", "")
    knowledge_snippets = state["knowledge_snippets"]

    prompt = ANSWER_PROMPT.format(
        memory_summary=memory_summary,
        chat_history=chat_history,
        knowledge_snippets=knowledge_snippets,
        question=question,
    )

    answer = llm.invoke(prompt)
    answer_text = str(answer).strip()
    state["messages"].append({"role": "assistant", "content": answer_text})
    return state


# ====================== Orchestrator ====================== #

def run_conversation_turn(
    user_input: str,
    llm: HFChatModel,
    vector_store: Chroma,
    metadata: Optional[Dict[str, Any]] = None,
    prev_state: Optional[ConversationState] = None,
) -> ConversationState:
    if metadata is None:
        metadata = {"client_type": "cardholder"}

        # --- Polite/small-talk shortcut ---
        normalized = user_input.lower().strip()
        small_talk = {"thanks", "thank you", "thx", "ty", "grazie", "ok", "okay"}

        if normalized in small_talk:
            # If we have previous state, just append a short reply without going through RAG
            if prev_state is None:
                state: ConversationState = {
                    "messages": [{"role": "user", "content": user_input}],
                    "user_input_reph": "",
                    "knowledge_snippets": "",
                    "metadata": metadata,
                    "memory_summary": "",
                }
            else:
                state = prev_state
                state["messages"].append({"role": "user", "content": user_input})
                state["metadata"] = metadata

            reply = "You're welcome! If you have any other questions, feel free to ask."
            state["messages"].append({"role": "assistant", "content": reply})
            return state

    if prev_state is None:
        state: ConversationState = {
            "messages": [{"role": "user", "content": user_input}],
            "user_input_reph": "",
            "knowledge_snippets": "",
            "metadata": metadata,
            "memory_summary": "",
        }
    else:
        state = prev_state
        state["messages"].append({"role": "user", "content": user_input})
        state["metadata"] = metadata

    state = rephrase_node(state, llm=llm)
    state = retrieval_node(state, vector_store=vector_store)
    state = answer_node(state, llm=llm)
    state = update_memory_summary(state, llm=llm)

    return state


def print_conversation_state(state: ConversationState, show_snippets: bool = False) -> None:
    print("=== Conversation ===")
    for m in state["messages"]:
        print(f'{m["role"].upper()}: {m["content"]}')

    if show_snippets:
        print("\n=== Knowledge snippets ===")
        print(state["knowledge_snippets"] or "[none]")

    if state.get("memory_summary"):
        print("\n=== Memory summary ===")
        print(state["memory_summary"])


# ====================== CLI main ====================== #

if __name__ == "__main__":
    embedding_model = build_embedding_model()
    vector_store = attach_vector_store()
    llm = build_llm()

    print("RAG Chatbot (HF Inference + Chroma)")
    print("Type 'exit' or 'quit' to stop.\n")

    default_client_type = "cardholder"
    chosen = input("Client type [cardholder / merchant] (default cardholder): ").strip().lower()
    client_type = chosen if chosen in ("cardholder", "merchant") else default_client_type
    print(f"Using client_type = '{client_type}'\n")

    conv_state: Optional[ConversationState] = None

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            assistant_reply = "Assistant: Bye! 👋"
            print(f"Assistant: {assistant_reply}\n")
            break
        if user_input.lower() in ("thanks", "thank you", "thank", "thx", "grazie"):
            assistant_reply = "You're welcome! Can I help you with anything else?"
            print(f"Assistant: {assistant_reply}\n")
            continue
        if not user_input:
            continue

        conv_state = run_conversation_turn(
            user_input=user_input,
            llm=llm,
            vector_store=vector_store,
            metadata={"client_type": client_type},
            prev_state=conv_state,
        )

        assistant_reply = conv_state["messages"][-1]["content"]
        print(f"Assistant: {assistant_reply}\n")
