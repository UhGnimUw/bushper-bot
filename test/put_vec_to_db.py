#!/usr/bin/env python
"""将文档存入 ChromaDB 向量库（支持分级 Collection）。

用法：
    # 单文件存入指定 tier
    python test/put_vec_to_db.py -f path/to/doc.txt -l tier0
    python test/put_vec_to_db.py -f doc.md -l tier1

    # 目录批量存入指定 tier
    python test/put_vec_to_db.py -d /path/to/docs -l tier2

    # 文本直接存入
    python test/put_vec_to_db.py -t "文本内容" -l tier3

    # 清空后存入
    python test/put_vec_to_db.py -f doc.txt -l tier1 --clear
"""
import argparse
import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import sys
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from src.agent.llm import embedding_model


# 添加项目根目录到 sys.path


PERSIST_DIR = "./chroma_db"
DEFAULT_COLLECTION = "rag_collection"
CHUNK_SIZE = 300
CHUNK_OVERLAP = 30

VALID_TIERS = ["tier0", "tier1", "tier2", "tier3"]


def load_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8")
    elif suffix in (".md", ".markdown"):
        return path.read_text(encoding="utf-8")
    elif suffix == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            print("pypdf 未安装，无法读取 PDF 文件。")
            raise
    elif suffix in (".docx", ".doc"):
        try:
            import docx
            doc = docx.Document(str(path))
            return "\n".join(para.text for para in doc.paragraphs)
        except ImportError:
            print("python-docx 未安装，无法读取 Word 文件。")
            raise
    else:
        raise ValueError(f"不支持的文件类型：{suffix}")


def collect_files(directory: str) -> list[Path]:
    """Recursively collect all supported files from a directory."""
    path = Path(directory)
    if not path.is_dir():
        return []
    suffixes = {".txt", ".md", ".markdown", ".pdf", ".docx", ".doc"}
    files = []
    for suf in suffixes:
        files.extend(path.rglob(f"*{suf}"))
    return sorted(files)


def put_file(file_path: str, collection_name: str, clear: bool):
    """Store a single file into ChromaDB collection."""
    path = Path(file_path)
    if not path.exists():
        print(f"文件不存在：{path}")
        return

    print(f"读取文档：{path}")
    content = load_document(path)
    if not content.strip():
        print("文档内容为空。")
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    texts = text_splitter.create_documents([content], metadata={"source": str(path)})

    chromadb = Chroma(
        persist_directory=PERSIST_DIR,
        collection_name=collection_name,
        embedding_function=embedding_model,
    )

    if clear:
        print(f"清空集合 {collection_name}...")
        chromadb.delete_collection()
        chromadb = Chroma(
            persist_directory=PERSIST_DIR,
            collection_name=collection_name,
            embedding_function=embedding_model,
        )

    print(f"切分文档为 {len(texts)} 个 chunk，存入集合 {collection_name}...")
    chromadb.from_documents(
        texts,
        embedding_model,
        persist_directory=PERSIST_DIR,
        collection_name=collection_name,
    )
    print("存入完成。")


def put_text(text: str, collection_name: str, clear: bool):
    """Store raw text into ChromaDB collection."""
    if not text.strip():
        print("文本内容为空。")
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    texts = text_splitter.create_documents([text])

    chromadb = Chroma(
        persist_directory=PERSIST_DIR,
        collection_name=collection_name,
        embedding_function=embedding_model,
    )

    if clear:
        print(f"清空集合 {collection_name}...")
        chromadb.delete_collection()
        chromadb = Chroma(
            persist_directory=PERSIST_DIR,
            collection_name=collection_name,
            embedding_function=embedding_model,
        )

    print(f"切分文本为 {len(texts)} 个 chunk，存入集合 {collection_name}...")
    chromadb.from_documents(
        texts,
        embedding_model,
        persist_directory=PERSIST_DIR,
        collection_name=collection_name,
    )
    print("存入完成。")


def put_directory(dir_path: str, collection_name: str, clear: bool):
    """Store all supported files from a directory into ChromaDB collection."""
    files = collect_files(dir_path)
    if not files:
        print(f"目录中未找到可处理的文件：{dir_path}")
        return

    print(f"找到 {len(files)} 个文件，存入集合 {collection_name}...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    if clear:
        chromadb = Chroma(
            persist_directory=PERSIST_DIR,
            collection_name=collection_name,
            embedding_function=embedding_model,
        )
        print(f"清空集合 {collection_name}...")
        chromadb.delete_collection()

    total_chunks = 0
    for i, file_path in enumerate(files, 1):
        try:
            content = load_document(file_path)
            if not content.strip():
                continue
            texts = text_splitter.create_documents(
                [content], metadata={"source": str(file_path)}
            )
            Chroma.from_documents(
                texts,
                embedding_model,
                persist_directory=PERSIST_DIR,
                collection_name=collection_name,
            )
            total_chunks += len(texts)
            print(f"  [{i}/{len(files)}] {file_path.name} → {len(texts)} chunks")
        except Exception as e:
            print(f"  [{i}/{len(files)}] {file_path.name} → 失败：{e}")

    print(f"存入完成，共 {total_chunks} 个 chunk。")


def main():
    parser = argparse.ArgumentParser(description="将文档存入 ChromaDB 向量库（支持分级）")
    parser.add_argument("-f", "--file", help="文件路径（支持 .txt .md .pdf .docx）")
    parser.add_argument("-d", "--dir", help="目录路径（批量存入）")
    parser.add_argument("-t", "--text", help="直接传入文本内容")
    parser.add_argument(
        "-l", "--level", default="tier3",
        help=f"权限层级 collection 名称（默认：tier3），可选：{', '.join(VALID_TIERS)}"
    )
    parser.add_argument(
        "-c", "--collection",
        help="直接指定 collection 名称（优先级高于 -l）"
    )
    parser.add_argument("--clear", action="store_true", help="存入前清空集合")
    args = parser.parse_args()

    # Resolve collection name
    if args.collection:
        collection_name = args.collection
    else:
        if args.level not in VALID_TIERS:
            print(f"无效层级：{args.level}，可选：{', '.join(VALID_TIERS)}")
            return
        collection_name = args.level

    if args.dir:
        put_directory(args.dir, collection_name, args.clear)
    elif args.file:
        put_file(args.file, collection_name, args.clear)
    elif args.text:
        put_text(args.text, collection_name, args.clear)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
