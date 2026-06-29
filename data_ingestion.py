import os
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def ingest_data(company_path, project_path):
    all_documents = []
    
    # 1. Quét dữ liệu chung của công ty
    print(f"Đang quét thư mục công ty: {company_path}")
    if os.path.exists(company_path):
        # Dùng **/*.pdf để quét cả thư mục con nếu có
        loader_company = DirectoryLoader(company_path, glob="**/*.pdf", loader_cls=PyPDFLoader)
        docs_company = loader_company.load()
        # Gắn thẻ (Metadata) để AI biết đây là chuẩn mực chung
        for doc in docs_company:
            doc.metadata["source_type"] = "company_standard"
        all_documents.extend(docs_company)
        print(f"-> Đã nạp {len(docs_company)} tài liệu công ty.")

    # 2. Quét dữ liệu dự án theo Mã Dự Án
    print(f"\nĐang quét thư mục dự án: {project_path}")
    if os.path.exists(project_path):
        loader_project = DirectoryLoader(project_path, glob="**/*.pdf", loader_cls=PyPDFLoader)
        docs_project = loader_project.load()
        
        for doc in docs_project:
            doc.metadata["source_type"] = "project_specific"
            
            # Trích xuất Mã dự án từ tên thư mục chứa file
            # Ví dụ: data/project_info/DinhVilla68/file.pdf -> Lấy chữ 'DinhVilla68'
            path_parts = doc.metadata["source"].replace("\\", "/").split("/")
            try:
                # Tìm chữ 'project_info' trên đường dẫn và lấy thư mục ngay sau nó
                idx = path_parts.index("project_info")
                project_code = path_parts[idx + 1]
                # Nếu file nằm trơ trọi không có thư mục con, nó sẽ lấy luôn tên file, ta cần tránh
                if project_code.endswith(".pdf"):
                    project_code = "Khong_Co_Ma_Du_An"
                doc.metadata["project_code"] = project_code
            except ValueError:
                doc.metadata["project_code"] = "unknown"
                
        all_documents.extend(docs_project)
        print(f"-> Đã nạp {len(docs_project)} tài liệu dự án.")

    if not all_documents:
        print("\nKhông tìm thấy tài liệu nào! Vui lòng kiểm tra lại thư mục.")
        return None

    # 3. Cắt nhỏ dữ liệu (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(all_documents)
    
    # 4. Chuyển hóa thành Vector (Sử dụng Local Model miễn phí)
    hf_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # 5. Lưu vào ChromaDB
    vector_db = Chroma.from_documents(
        documents=chunks, 
        embedding=hf_embeddings,
        persist_directory="./chroma_db"
    )
    print("\n✅ TOÀN BỘ DỮ LIỆU ĐÃ ĐƯỢC NẠP VÀ GẮN THẺ THÀNH CÔNG!")
    return vector_db

if __name__ == "__main__":
    # Đã cập nhật đúng tên thư mục theo yêu cầu của bạn
    ingest_data("./data/company_info", "./data/project_info")