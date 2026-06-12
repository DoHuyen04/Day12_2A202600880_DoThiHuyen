# Đánh Giá Chất Lượng Retrieval

## Vì sao cần đánh giá

Một hệ thống retrieval có thể chạy không lỗi nhưng vẫn trả về kết quả kém. Vì
vậy, thay vì chỉ hỏi "code có chạy không", ta cần đo "retrieval tốt đến đâu".
Đánh giá có hệ thống giúp so sánh các chiến lược chunking, lựa chọn metadata, và
mô hình embedding một cách khách quan, thay vì dựa vào cảm tính.

## Retrieval precision

Precision đo trong số các kết quả trả về, bao nhiêu kết quả thật sự liên quan.
Với top-3, mục tiêu là có ít nhất hai chunk liên quan trực tiếp đến câu hỏi.
Ngoài ra, cần xem phân bố điểm số: nếu điểm của kết quả tốt và kết quả nhiễu gần
bằng nhau, hệ thống khó phân biệt được đâu là thông tin đáng tin.

## Chunk coherence

Chunk coherence đánh giá mức độ trọn vẹn về ngữ nghĩa của mỗi chunk. Một chunk
tốt giữ nguyên một ý hoàn chỉnh, không bị cắt giữa câu hay giữa ý. Khi so sánh
các chiến lược, hãy nhìn vào số lượng chunk và độ dài trung bình, đồng thời đọc
thử vài chunk để cảm nhận chúng có dễ hiểu khi đứng một mình hay không.

## Metadata utility

Metadata utility đo mức hữu ích của việc lọc theo metadata. Hãy chạy cùng một câu
hỏi với tìm kiếm thường và tìm kiếm có lọc, ví dụ lọc theo ngôn ngữ hoặc chủ đề,
rồi so sánh top-3. Lọc đúng giúp loại nhiễu và tăng độ chính xác, nhưng lọc quá
chặt có thể vô tình loại bỏ những kết quả tốt, nên cần cân bằng.

## Grounding quality

Grounding quality kiểm tra câu trả lời của trợ lý có thật sự dựa trên context
được truy xuất hay không. Một cách đơn giản là đối chiếu câu trả lời với đáp án
chuẩn trong bộ benchmark, đồng thời chỉ ra chunk nào đã hỗ trợ câu trả lời. Nếu
không thể truy vết câu trả lời về một chunk cụ thể, nhiều khả năng mô hình đang
bịa.

## Phân tích thất bại

Mỗi lần đánh giá nên tìm ít nhất một trường hợp thất bại và mô tả rõ. Câu hỏi nào
retrieval kém, và vì sao: chunk quá nhỏ hay quá lớn, metadata thiếu, hay câu hỏi
mơ hồ. Sau đó đề xuất cách cải thiện, chẳng hạn đổi kích thước chunk, bổ sung
metadata, hoặc viết lại câu hỏi rõ ràng hơn. Chính những phân tích này tạo ra
bài học giá trị nhất.
