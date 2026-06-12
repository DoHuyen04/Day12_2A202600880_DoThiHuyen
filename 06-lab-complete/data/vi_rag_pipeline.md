# Pipeline RAG Cho Trợ Lý Tri Thức

## RAG là gì

RAG, viết tắt của retrieval-augmented generation, là kiến trúc kết hợp tìm kiếm
tài liệu với sinh văn bản. Thay vì để mô hình ngôn ngữ trả lời chỉ dựa trên trí
nhớ, RAG truy xuất các đoạn tài liệu liên quan trước, rồi đưa chúng vào prompt để
mô hình bám sát nguồn dữ liệu. Cách làm này giúp câu trả lời chính xác hơn, cập
nhật hơn, và có thể truy vết nguồn.

## Các bước trong pipeline

Một pipeline RAG điển hình gồm năm bước nối tiếp nhau. Bước một, chia tài liệu
thành các chunk có kích thước hợp lý. Bước hai, tạo embedding cho từng chunk và
lưu vào vector store cùng metadata. Bước ba, khi có câu hỏi, tạo embedding cho
câu hỏi và truy xuất các chunk gần nhất. Bước bốn, ghép các chunk thành khối
context và dựng prompt. Bước năm, gọi mô hình ngôn ngữ để sinh câu trả lời dựa
trên context đó.

## Vai trò của chunking

Chunking quyết định chất lượng của toàn bộ pipeline. Nếu chunk quá lớn, embedding
bị loãng và kết quả trả về cả những phần không liên quan. Nếu chunk quá nhỏ, mỗi
chunk thiếu ngữ cảnh và mô hình khó ghép nối thông tin. Một chiến lược tốt nên
cắt theo ranh giới tự nhiên như câu hoặc đoạn, để mỗi chunk giữ trọn một ý.

## Vai trò của grounding

Grounding nghĩa là câu trả lời phải dựa trên context đã truy xuất chứ không phải
do mô hình bịa ra. Để tăng grounding, prompt nên yêu cầu rõ ràng "chỉ trả lời
dựa trên context bên dưới" và đánh số các chunk để mô hình có thể trích dẫn. Nếu
không truy xuất được chunk nào liên quan, hệ thống nên trả về thông báo không tìm
thấy thay vì đoán bừa.

## Đánh giá pipeline

Đừng chỉ hỏi "hệ thống có chạy không" mà hãy hỏi "retrieval tốt đến đâu". Hãy
chuẩn bị một bộ câu hỏi benchmark kèm đáp án chuẩn, chạy chúng qua pipeline, rồi
kiểm tra xem top-3 kết quả có chứa chunk thật sự liên quan không và câu trả lời
có bám đúng đáp án không. Quan sát có hệ thống như vậy giúp phát hiện điểm yếu và
cải thiện từng bước.
