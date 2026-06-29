import re  # Đảm bảo đã import thư viện re ở đầu file
import os
import pandas as pd
from duckduckgo_search import DDGS
from langchain_community.document_loaders import PyPDFLoader
import time
import requests  # Thêm thư viện để gọi Local Server
import json      # Thêm thư viện để xử lý dữ liệu AI trả về
from openai import OpenAI
from dotenv import load_dotenv

# Tải cấu hình từ file .env
load_dotenv()

def read_research_requirements(pdf_path):
    print("\n[1] ĐANG ĐỌC YÊU CẦU TỪ PDF...")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    content = " ".join([doc.page_content for doc in docs])
    return content

def generate_research_plan(pdf_content):
    print("\n[2] BỘ NÃO OPENAI ĐANG PHÂN TÍCH YÊU CẦU...")
    
    # Khởi tạo client OpenAI
    client = OpenAI()
    
    # Đã sửa lại Prompt: Bỏ giới hạn 5 từ khóa, yêu cầu lấy TOÀN BỘ
    system_prompt = f"""
    Bạn là một Đặc vụ AI Phân tích Dữ liệu. Hãy đọc kỹ tài liệu yêu cầu dưới đây và lập kế hoạch thu thập dữ liệu tự động.
    
    TÀI LIỆU YÊU CẦU CỦA NGƯỜI DÙNG:
    {pdf_content}
    
    NHIỆM VỤ CỦA BẠN:
    1. Trích xuất chính xác Mã Dự Án.
    2. Trích xuất TOÀN BỘ các "Từ khóa mồi" (Seed Keywords) đã được người dùng liệt kê trong tài liệu. Không được tự ý cắt giảm.
    LUẬT CỨNG: Nếu từ khóa nào quá dài mang tính chất văn nói, hãy tự động rút gọn lại thành từ khóa CHUẨN SEO (2-6 chữ). Nếu từ khóa đã ngắn gọn, hãy giữ nguyên.
    
    TRẢ VỀ ĐÚNG ĐỊNH DẠNG JSON NHƯ SAU:
    {{
        "ma_du_an": "Mã tìm được",
        "tom_tat_muc_tieu": "1 câu tóm tắt",
        "danh_sach_tu_khoa": ["Từ khóa 1", "Từ khóa 2", "Từ khóa 3", "...", "Từ khóa thứ N"]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  
            messages=[{"role": "user", "content": system_prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        plan_data = json.loads(response.choices[0].message.content)
        return plan_data
        
    except Exception as e:
        print(f"-> Gặp sự cố kết nối OpenAI: {e}")
        return {
            "ma_du_an": "ATCT2506",
            "tom_tat_muc_tieu": "Lỗi API - Mẫu dự phòng",
            "danh_sach_tu_khoa": ["áo thun Justdun", "review Justdun TikTok", "doanh thu Justdun Metric"]
        }

def ask_for_approval(plan_data):
    print("\n" + "="*40)
    print("📋 BẢN KẾ HOẠCH TRIỂN KHAI NGHIÊN CỨU")
    print("="*40)
    # Hiển thị dữ liệu do AI bóc tách
    print(f"- Mã dự án: {plan_data.get('ma_du_an', 'Không rõ')}")
    print(f"- Mục tiêu: {plan_data.get('tom_tat_muc_tieu', '')}")
    print("- Danh sách từ khóa tìm kiếm:")
    for idx, kw in enumerate(plan_data.get('danh_sach_tu_khoa', []), 1):
        print(f"  {idx}. {kw}")
    print("="*40)
    
    # Lớp khiên bảo vệ: Chờ phê duyệt trước khi bật chế độ giám sát
    while True:
        confirm = input("\nBạn có xác nhận triển khai kế hoạch và bật chế độ giám sát không? (y/n): ").strip().lower()
        if confirm == 'y':
            return True
        elif confirm == 'n':
            return False
        print("Vui lòng nhập 'y' hoặc 'n'.")

def continuous_scraping_loop(search_queries, output_excel_path):
    print("\n[+] ĐÃ BẬT CHẾ ĐỘ GIÁM SÁT VÀ THU THẬP LIÊN TỤC...")
    from duckduckgo_search import DDGS
    import time
    import os
    import pandas as pd
    import json
    from openai import OpenAI
    
    # Khởi tạo bộ não AI để đọc và bóc tách dữ liệu từng bài viết
    client = OpenAI()
    
    # ĐỊNH NGHĨA CHÍNH XÁC CÁC CỘT THEO TIÊU CHUẨN CỦA BẠN 
    # (Tôi thêm 2 cột Nguồn và Trích đoạn gốc ở cuối để bạn có thể kiểm chứng số liệu)
    columns = [
        "Chu Kỳ", "Từ Khóa", 
        "Tên loại áo", "Số lượng mua", "Độ tuổi trung bình", "Khu vực mua nhiều nhất", "Mua ở kênh nào",
        "Nguồn (URL)", "Trích Đoạn Gốc"
    ]
    all_collected_data = []
    cycle = 1
    
    if os.path.exists(output_excel_path):
        try:
            existing_df = pd.read_excel(output_excel_path)
            all_collected_data = existing_df.to_dict('records')
        except Exception:
            pass

    with DDGS() as ddgs:
        while True:
            print(f"\n--- Chu kỳ thu thập thứ {cycle} ---")
            found_in_this_cycle = False 
            
            for query in search_queries:
                print(f"Đang dò tìm: '{query}'", end="... ")
                try:
                    results = list(ddgs.text(query, max_results=3))
                    
                    if not results:
                        print("❌ 0 kết quả")
                        time.sleep(3)
                        continue
                        
                    print(f"✅ Thấy {len(results)} kết quả. Bắt đầu nhờ AI phân loại vào cột...")
                    
                    for res in results:
                        raw_title = res.get("title", "")
                        raw_body = res.get("body", "")
                        url = res.get("href", "")
                        
                        # ----- BƯỚC ĐỘT PHÁ: GIAO VIỆC CHO AI ĐỌC DỮ LIỆU -----
                        extraction_prompt = f"""
                        Bạn là chuyên gia nhập liệu thị trường. Hãy đọc đoạn thông tin cào được dưới đây và trích xuất vào các trường tương ứng. 
                        Nếu thông tin không đề cập đến một trường nào đó, hãy điền "Chưa rõ".

                        THÔNG TIN CÀO ĐƯỢC:
                        Tiêu đề: {raw_title}
                        Nội dung: {raw_body}

                        TRẢ VỀ ĐÚNG ĐỊNH DẠNG JSON NÀY:
                        {{
                            "ten_loai_ao": "Tên sản phẩm",
                            "so_luong_mua": "Doanh số/Lượt mua",
                            "do_tuoi_trung_binh": "Tuổi/Tệp khách hàng",
                            "khu_vuc_mua_nhieu_nhat": "Khu vực",
                            "mua_o_kenh_nao": "Shopee/TikTok/Facebook/..."
                        }}
                        """
                        try:
                            # Sử dụng gpt-4o-mini để xử lý cực nhanh và rẻ cho các vòng lặp lớn
                            ai_response = client.chat.completions.create(
                                model="gpt-4o-mini", 
                                messages=[{"role": "user", "content": extraction_prompt}],
                                response_format={"type": "json_object"},
                                temperature=0.1
                            )
                            extracted = json.loads(ai_response.choices[0].message.content)
                        except Exception:
                            # Xử lý lỗi nếu AI từ chối phản hồi
                            extracted = {}

                        # Đổ dữ liệu đã được AI "nhặt" vào đúng các cột Excel
                        all_collected_data.append({
                            "Chu Kỳ": cycle,
                            "Từ Khóa": query,
                            "Tên loại áo": extracted.get("ten_loai_ao", "Chưa rõ"),
                            "Số lượng mua": extracted.get("so_luong_mua", "Chưa rõ"),
                            "Độ tuổi trung bình": extracted.get("do_tuoi_trung_binh", "Chưa rõ"),
                            "Khu vực mua nhiều nhất": extracted.get("khu_vuc_mua_nhieu_nhat", "Chưa rõ"),
                            "Mua ở kênh nào": extracted.get("mua_o_kenh_nao", "Chưa rõ"),
                            "Nguồn (URL)": url,
                            "Trích Đoạn Gốc": raw_body
                        })
                        
                    found_in_this_cycle = True
                    time.sleep(4) 
                except Exception as e:
                    print(f"❌ Lỗi: {e}")
                    time.sleep(4)
            
            # Xuất ra File Excel hoàn chỉnh
            if all_collected_data:
                df = pd.DataFrame(all_collected_data, columns=columns)
            else:
                df = pd.DataFrame(columns=columns)
                
            try:
                df.to_excel(output_excel_path, index=False)
                if found_in_this_cycle:
                    print(f"\n-> 💾 Đã phân loại và đổ dữ liệu thành công vào bảng Excel!")
            except PermissionError:
                print(f"\n[⛔ LỖI QUYỀN TRUY CẬP] Hãy TẮT file Excel đang mở để hệ thống có thể lưu đè!")
            
            stop_command = input("\nHệ thống đang giám sát. Nhấn 'Enter' để quét chu kỳ tiếp, hoặc gõ 'stop' để dừng: ").strip().lower()
            if stop_command == 'stop':
                break
            cycle += 1
            
    return output_excel_path

def generate_final_report(excel_data_path, company_db_path, project_db_path):
    print("\n[3] ĐANG NẠP DỮ LIỆU EXCEL VÀO BỘ NÃO AI...")
    import pandas as pd
    from openai import OpenAI
    import os

    # 1. Kiểm tra file Excel
    if not os.path.exists(excel_data_path):
        print(f"❌ Không tìm thấy file dữ liệu: {excel_data_path}")
        return

    # 2. Đọc và "tiêu hóa" dữ liệu
    try:
        df = pd.read_excel(excel_data_path)
        if df.empty:
            print("⚠️ File Excel đang trống, AI sẽ không có dữ liệu thực tế để trả lời.")
            data_context = "Dữ liệu hiện tại đang trống."
        else:
            # Chuyển đổi toàn bộ bảng Excel thành định dạng JSON để AI hiểu dễ nhất
            data_context = df.to_json(orient="records", force_ascii=False)
    except Exception as e:
        print(f"❌ Lỗi đọc file Excel: {e}")
        return

    # 3. Khởi tạo OpenAI và thiết lập "Trí nhớ" ban đầu
    client = OpenAI()
    
    # Ép AI đóng vai và "nhập tâm" toàn bộ dữ liệu Excel vào đầu
    messages = [
        {
            "role": "system", 
            "content": f"Bạn là một Chuyên gia Nghiên cứu Thị trường dữ liệu xuất sắc. Dưới đây là kho dữ liệu thị trường mới nhất vừa được hệ thống tự động cào về:\n\n{data_context}\n\nNhiệm vụ của bạn là trả lời các câu hỏi, phân tích số liệu, hoặc xuất báo cáo TÙY THEO YÊU CẦU CỦA NGƯỜI DÙNG. Tuyệt đối bám sát vào dữ liệu được cung cấp, không bịa đặt số liệu ảo ngoài file."
        }
    ]
    
    print("\n✅ BỘ NÃO AI ĐÃ HỌC XONG DỮ LIỆU TỪ EXCEL!")
    print("="*70)
    print("💬 CHAT BOT PHÂN TÍCH THỊ TRƯỜNG (Gõ 'stop' hoặc 'exit' để thoát)")
    print("Gợi ý lệnh: 'Viết báo cáo tổng quan', 'Kênh nào bán chạy nhất?', 'Độ tuổi mua hàng là bao nhiêu?'")
    print("="*70)
    
    # 4. Vòng lặp Chat trực tiếp với AI
    while True:
        user_prompt = input("\n👉 Bạn muốn hỏi gì hoặc xuất báo cáo gì?: ").strip()
        
        if user_prompt.lower() in ['stop', 'exit', 'thoát']:
            print("Đã đóng phiên làm việc với AI. Hẹn gặp lại!")
            break
            
        if not user_prompt:
            continue
            
        # Thêm câu hỏi của bạn vào lịch sử trò chuyện
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            print("Đang suy nghĩ...")
            # Sử dụng gpt-4o để có khả năng tư duy dữ liệu sắc bén nhất
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.3  # Hạ nhiệt độ để AI trả lời chính xác, bớt bay bổng
            )
            
            ai_reply = response.choices[0].message.content
            print("\n🤖 AI TRẢ LỜI:")
            print(ai_reply)
            
            # Thêm câu trả lời của AI vào lịch sử để nó nhớ được luồng trò chuyện cho câu hỏi tiếp theo
            messages.append({"role": "assistant", "content": ai_reply})
            
        except Exception as e:
            print(f"❌ Lỗi kết nối OpenAI: {e}")
            # Lấy lại tin nhắn cuối cùng nếu bị lỗi để không hỏng lịch sử
            messages.pop()

if __name__ == "__main__":
    collected_data_dir = "./data/collected_data"
    os.makedirs(collected_data_dir, exist_ok=True)

    excel_output = os.path.join(collected_data_dir, "DuLieu_ThuThap_ThiTruong.xlsx")

    # TỰ ĐỘNG QUÉT TẤT CẢ FILE .PDF TRONG THƯ MỤC COLLECTED_DATA
    pdf_files = [f for f in os.listdir(collected_data_dir) if f.endswith('.pdf')]

    if not pdf_files:
        print(f"\n[CẢNH BÁO] Không tìm thấy file PDF yêu cầu nào trong thư mục: {collected_data_dir}")
        print("Vui lòng bỏ ít nhất 1 file PDF mô tả yêu cầu nghiên cứu của bạn vào đây.")
    else:
        # Lấy file PDF đầu tiên tìm thấy để tiến hành nghiên cứu
        target_pdf = os.path.join(collected_data_dir, pdf_files[0])
        print(f"\n🎯 Đã tìm thấy file yêu cầu: {pdf_files[0]}")

        # 1. Đọc PDF
        req_content = read_research_requirements(target_pdf)

        # 2. Gọi Local LLM để phân tích PDF và lên Kế hoạch
        plan_data = generate_research_plan(req_content)
        keywords = plan_data.get("danh_sach_tu_khoa", [])

        # 3. Yêu cầu xác nhận trước khi chạy giám sát
        is_approved = ask_for_approval(plan_data)

        if is_approved:
            # 4. Chạy chế độ giám sát liên tục & xuất Excel
            if keywords:
                continuous_scraping_loop(keywords, excel_output)
                # 5. Phân tích chéo và ra báo cáo
                generate_final_report(excel_output, "./chroma_db", "./chroma_db")
            else:
                print("\nLỗi: Không có từ khóa nào được tạo ra để tìm kiếm.")
        else:
            print("Đã hủy triển khai. Chờ chỉ thị mới.")