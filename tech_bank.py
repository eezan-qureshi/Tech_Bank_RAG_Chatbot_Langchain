"""
LangChain parts used:
    PyPDFLoader                    -> load the PDF (one Document per page)
    RecursiveCharacterTextSplitter -> chunking
    Embeddings (Chroma ONNX model) -> embedding
    Chroma (langchain_chroma)      -> vector database saved on disk, + retriever
    ChatPromptTemplate | ChatGroq | StrOutputParser -> chains (LCEL)
    HumanMessage / AIMessage       -> chat memory (saved in chat_memory.json)

"""

import argparse
import json
import os
import re
import sys

from dotenv import load_dotenv

load_dotenv()   # reads GROQ_API_KEY from the .env file

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage, HumanMessage, messages_from_dict, messages_to_dict
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ------------------------------------------------------------------ settings
MODEL = "openai/gpt-oss-120b"      # change if Groq says 'model not found'
DB_FOLDER = "tech_bank_lc_db"      # the vector database is saved in this folder
COLLECTION = "tech_bank_kb"
MEMORY_FILE = "chat_memory.json"   # the chat memory is saved here
MAX_CHARS = 400                    # biggest chunk size
CHUNK_OVERLAP = 40                 # only used when a long item has to be cut further
N_RESULTS = 4                      # chunks given to the model per question
HISTORY_MESSAGES = 10              # last 5 questions + 5 answers are remembered
OFF_TOPIC = "OFF_TOPIC"            # router marker: clearly unrelated to banking
SMALL_TALK = "SMALL_TALK"          # router marker: greetings, thanks, introductions

# Only a tiny, generic instruction lives in the code.
# The real bank policies and chatbot rules come from the PDF (retrieved as context).
RULES = (
    "You are Tech Bank's virtual assistant. "
    "Use ONLY the context given to you (it comes from Tech Bank's official policy document). "
    "Follow any chatbot rules, tone or restrictions that appear in the context. "
    "If the question is about banking but the answer is not in the context, say politely that you "
    "don't have that information and suggest contacting a Tech Bank branch or helpline. "
    "Never invent facts, numbers or fees. "
    "The earlier chat messages may contain details the user told you (for example their name). "
    "If the user asks about such a detail, answer it from the chat history."
)

ROUTER_RULES = (
    "You sort the user's last message into one of three kinds. Use the chat history for context.\n"
    "A) SMALL TALK: greetings, 'how are you', thanks, goodbye, or the user telling you something "
    "about themselves (for example their name), or the user asking about something they told you "
    "earlier in this chat (for example 'what is my name?'). Output exactly " + SMALL_TALK + ".\n"
    "B) OFF TOPIC: the user asks for information or help that has nothing to do with banking "
    "(for example sports results, politics, movies, general knowledge, coding, cooking, health). "
    "Output exactly " + OFF_TOPIC + ". Use this ONLY for a clear question or request on an unrelated "
    "subject. When in doubt, do NOT use it.\n"
    "C) BANKING: anything about banking, Tech Bank, its services, or the assistant itself. Rewrite it "
    "as ONE standalone English search query for a bank policy document, filling in missing details "
    "from the chat history and translating to English if needed. Output only the query.\n"
    "Output nothing else."
)

DECLINE_RULES = (
    "You are Tech Bank's virtual assistant. The user asked something unrelated to banking. "
    "Do NOT answer it. In one or two short, polite sentences say that this question is out of "
    "context and that you can assist with banking questions about Tech Bank "
    "(accounts, cards, loans, fees, digital banking, security)."
)

SMALL_TALK_RULES = (
    "You are Tech Bank's friendly virtual assistant. Reply warmly in one or two short sentences. "
    "If the user tells you their name, greet them by name. If the user asks about something they "
    "told you earlier (for example their name), answer it from the chat history. Then offer to help "
    "with Tech Bank questions (accounts, cards, loans, fees, digital banking). Do not state any bank facts."
)


def language_note(question):
    """A clear language + script instruction, decided from how the user typed the question."""
    # Any letter outside the Latin alphabet (Urdu/Arabic script, Hindi, ...) -> same language and script
    if any(ch.isalpha() and ord(ch) > 0x024F for ch in question):
        return "LANGUAGE: reply in the same language AND script as the user's question."
    return ("LANGUAGE: the user typed in English letters. If the question is English, reply in English. "
            "If it is Roman Urdu (Urdu written in English letters), reply in Roman Urdu, "
            "using English letters ONLY. NEVER use Urdu/Arabic script in this reply.")


# ------------------------------------------------------------------ embeddings
class OnnxEmbeddings(Embeddings):
    """LangChain wrapper around Chroma's default (small, local) embedding model."""

    def __init__(self):
        self.fn = DefaultEmbeddingFunction()

    def embed_documents(self, texts):
        return [[float(x) for x in vector] for vector in self.fn(list(texts))]

    def embed_query(self, text):
        return self.embed_documents([text])[0]


# ------------------------------------------------------------------ 1 + 2. LOAD and CHUNK
def clean_text(text):
    return " ".join(text.split())


def split_items(text):
    """Cut at blank lines first. PDFs often have no blank lines, so also cut where a new
    policy item starts, i.e. after a full stop and before a 'Topic name:' label."""
    parts = []
    for block in re.split(r"\n\s*\n", text):
        block = clean_text(block)
        parts += re.split(r"(?<=[.!?])\s+(?=[A-Z][A-Za-z0-9'()/&, -]{2,60}:\s)", block)
    return parts


def build_chunks(pdf_path):
    pages = PyPDFLoader(pdf_path).load()
    source = os.path.basename(pdf_path)
    items = []
    for page in pages:
        number = int(page.metadata.get("page", 0)) + 1
        if not page.page_content.strip():
            print(f"  Skipped empty page (a scan? needs OCR): page {number}")
            continue
        for piece in split_items(page.page_content):
            piece = clean_text(piece)
            if piece:
                items.append(Document(page_content=piece, metadata={"source": source, "page": number}))
    # items that are still longer than MAX_CHARS are cut further; short ones stay whole
    splitter = RecursiveCharacterTextSplitter(chunk_size=MAX_CHARS, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_documents(items)


# ------------------------------------------------------------------ 3. EMBED + STORE
def ingest(pdf_path):
    if not os.path.isfile(pdf_path) or not pdf_path.lower().endswith(".pdf"):
        sys.exit(f"Error: '{pdf_path}' is not a PDF file that exists.")
    print(f"Reading {pdf_path} ...")
    chunks = build_chunks(pdf_path)
    if not chunks:
        sys.exit("Error: no text found in the PDF (scanned PDFs need OCR).")
    embeddings = OnnxEmbeddings()
    try:   # replace the old knowledge base
        Chroma(collection_name=COLLECTION, embedding_function=embeddings,
               persist_directory=DB_FOLDER).delete_collection()
    except Exception:
        pass
    store = Chroma.from_documents(documents=chunks, embedding=embeddings,
                                  collection_name=COLLECTION, persist_directory=DB_FOLDER)
    print(f"Done. {store._collection.count()} chunks embedded and saved in '{DB_FOLDER}/'.")
    print("Now run:  python tech_bank.py   to start chatting.")


def load_store():
    """Open the saved vector database. Returns None if the PDF was never loaded."""
    store = Chroma(collection_name=COLLECTION, embedding_function=OnnxEmbeddings(),
                   persist_directory=DB_FOLDER)
    return store if store._collection.count() > 0 else None


# ------------------------------------------------------------------ chat memory (saved on disk)
def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return messages_from_dict(json.load(f))
    except Exception:
        return []


def save_memory(messages):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(messages_to_dict(messages), f, ensure_ascii=False, indent=2)
    except OSError:
        pass        # memory is best-effort; the chat still works


# ------------------------------------------------------------------ 4 + 5. RETRIEVE and ANSWER (LCEL chains)
class TechBank:
    def __init__(self):
        if not os.environ.get("GROQ_API_KEY"):
            raise RuntimeError('GROQ_API_KEY not found. Put it in the .env file: GROQ_API_KEY="your_key"')
        self.store = load_store()
        if self.store is None:
            raise RuntimeError("No knowledge base found. Run once first:  "
                               "python tech_bank.py --pdf tech_bank_policies.pdf")
        self.retriever = self.store.as_retriever(search_kwargs={"k": N_RESULTS})

        def llm(temperature, max_tokens):
            return ChatGroq(model=MODEL, temperature=temperature, max_tokens=max_tokens)

        parser = StrOutputParser()
        history = MessagesPlaceholder("history")

        router_prompt = ChatPromptTemplate.from_messages(
            [("system", ROUTER_RULES), history, ("human", "{question}")])
        answer_prompt = ChatPromptTemplate.from_messages(
            [("system", RULES), history,
             ("human", "Context:\n{context}\n\nUser question: {question}\n\n{language_note}")])
        decline_prompt = ChatPromptTemplate.from_messages(
            [("system", DECLINE_RULES), ("human", "{question}\n\n{language_note}")])
        small_talk_prompt = ChatPromptTemplate.from_messages(
            [("system", SMALL_TALK_RULES), history, ("human", "{question}\n\n{language_note}")])

        # each chain:  prompt | model | parser
        self.router = router_prompt | llm(0, 300) | parser
        self.answerer = answer_prompt | llm(0, 1000) | parser
        self.decliner = decline_prompt | llm(0, 400) | parser
        self.chatter = small_talk_prompt | llm(0.3, 400) | parser

    def chunk_count(self):
        return self.store._collection.count()

    def reply(self, question, history):
        """Return (answer text, list of sources). `history` = recent HumanMessage/AIMessage list."""
        try:
            route = self.router.invoke({"history": history, "question": question}).strip() or question
        except Exception:
            route = question
        note = language_note(question)
        upper = route.upper()

        if SMALL_TALK in upper:
            return self.chatter.invoke({"history": history, "question": question, "language_note": note}), []
        if OFF_TOPIC in upper:
            return self.decliner.invoke({"question": question, "language_note": note}), []

        docs = self.retriever.invoke(route)       # search with the clean English query
        context = "\n\n".join(f"[Policy page {d.metadata['page']}]\n{d.page_content}" for d in docs)
        answer = self.answerer.invoke({"history": history, "question": question,
                                       "context": context, "language_note": note})
        sources = [{"page": d.metadata["page"], "text": d.page_content} for d in docs]
        return answer, sources


# ------------------------------------------------------------------ terminal chat
def chat():
    try:
        bot = TechBank()
    except RuntimeError as e:
        sys.exit(f"Error: {e}")
    memory = load_memory()

    print("=" * 60)
    print("  Welcome to Tech Bank Assistant (LangChain)")
    print("  Ask me anything about Tech Bank. Type 'exit' to quit.")
    print("  Type 'forget' to erase my memory of our past chats.")
    print("=" * 60)

    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! / Khuda hafiz!")
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q", "bye"}:
            print("Thank you for banking with Tech Bank. Goodbye!")
            break
        if question.lower() == "forget":
            memory = []
            save_memory(memory)
            print("Tech Bank: Memory cleared.")
            continue
        try:
            reply, sources = bot.reply(question, memory[-HISTORY_MESSAGES:])
        except Exception as e:
            print(f"Tech Bank: Sorry, something went wrong ({type(e).__name__}: {str(e)[:150]})")
            continue

        print(f"\nTech Bank: {reply}")
        if sources:
            pages = sorted({s["page"] for s in sources})
            print(f"(Source: policy document, page {', '.join(map(str, pages))})")

        memory += [HumanMessage(content=question), AIMessage(content=reply)]
        save_memory(memory[-100:])       # keep the file small


# ------------------------------------------------------------------ main
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tech Bank RAG chatbot (LangChain)")
    parser.add_argument("--pdf", help="Policy/rules PDF to load into the vector database (needed only once)")
    args = parser.parse_args()
    if args.pdf:
        ingest(args.pdf)
    else:
        chat()
