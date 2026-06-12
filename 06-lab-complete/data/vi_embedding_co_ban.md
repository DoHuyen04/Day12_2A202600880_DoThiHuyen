# Cơ Bản Về Embedding

## Embedding là gì

Embedding là một vector số thực có độ dài cố định, dùng để biểu diễn ý nghĩa của
một đoạn văn bản. Hai đoạn văn nói về cùng một ý sẽ tạo ra hai vector chỉ gần
cùng một hướng trong không gian ngữ nghĩa. Nhờ đặc điểm này, embedding là nền
tảng của tìm kiếm ngữ nghĩa: hệ thống có thể nối một câu hỏi với một câu trả lời
ngay cả khi chúng không dùng chung từ nào, miễn là chúng chia sẻ ý nghĩa.

## Khác biệt với tìm kiếm từ khóa

Tìm kiếm từ khóa truyền thống chỉ khớp khi các từ trùng nhau, nên dễ bỏ sót khi
người dùng diễn đạt theo cách khác. Ví dụ, câu hỏi "làm sao đặt lại mật khẩu"
có thể không khớp với tài liệu ghi "khôi phục tài khoản đăng nhập" dù chúng cùng
một chủ đề. Embedding giải quyết vấn đề này vì nó so khớp theo nghĩa chứ không
theo mặt chữ, giúp retrieval bao phủ được nhiều cách hỏi khác nhau.

## Cách tạo embedding

Để tạo embedding, ta đưa văn bản qua một mô hình ngôn ngữ đã được huấn luyện.
Mô hình đọc toàn bộ chuỗi và xuất ra một vector tóm tắt ý nghĩa. Một số mô hình
phổ biến gồm các mô hình chạy cục bộ như all-MiniLM-L6-v2 (384 chiều, miễn phí,
bảo mật dữ liệu) và các mô hình gọi qua API như text-embedding-3-small (1536
chiều, chất lượng cao, đa ngôn ngữ tốt nhưng tốn phí theo token).

## Chuẩn hóa vector

Phần lớn mô hình hiện đại trả về vector đã được chuẩn hóa về độ dài đơn vị. Khi
vector đã chuẩn hóa, dot product và cosine similarity cho cùng thứ hạng nên dùng
cách nào cũng được. Khi vector chưa chuẩn hóa, nên ưu tiên cosine similarity vì
nó chỉ so sánh hướng của vector, bỏ qua độ lớn. Trộn lẫn vector đã chuẩn hóa và
chưa chuẩn hóa trong cùng một kho sẽ tạo ra điểm số sai lệch.

## Lưu ý thực hành

Luôn embed câu hỏi bằng đúng mô hình đã embed tài liệu, nếu không hai vector sẽ
nằm ở hai không gian khác nhau và điểm số trở nên vô nghĩa. Nên lưu cache các
embedding đã tính để tránh tính lại tốn thời gian và chi phí. Cuối cùng, hãy nhớ
embedding chỉ nắm bắt chủ đề bề mặt chứ không suy luận sâu: hai câu cùng lĩnh vực
vẫn có thể đạt điểm thấp hơn dự đoán nếu chúng nói về hai khía cạnh khác nhau.
