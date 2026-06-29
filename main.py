def ask_for_approval(plan):
    print("--- KẾ HOẠCH NGHIÊN CỨU ---")
    print(plan)
    confirmation = input("Bạn có muốn triển khai kế hoạch này không? (y/n): ")
    return confirmation.lower() == 'y'

def main():
    # Bước 1: Nhận khung chủ đề từ người dùng
    topic = input("Nhập chủ đề cần nghiên cứu: ")
    
    # Bước 2: AI lập kế hoạch sơ bộ
    plan = f"Hệ thống sẽ cào dữ liệu từ [Nguồn A, B, C] về chủ đề: {topic}"
    
    # Bước 3: Chờ xác nhận
    if ask_for_approval(plan):
        print("Bắt đầu chế độ giám sát và thu thập dữ liệu...")
        # Gọi hàm scraper và phân tích tại đây
    else:
        print("Hệ thống đã dừng theo yêu cầu.")

if __name__ == "__main__":
    main()