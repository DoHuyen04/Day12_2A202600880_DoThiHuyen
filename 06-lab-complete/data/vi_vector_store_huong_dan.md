# Hướng Dẫn Về Vector Store

## Vector store là gì

Vector store là một lớp lưu trữ được thiết kế để giữ các embedding và truy xuất
nhanh những mục tương đồng nhất với một vector truy vấn. Trong các hệ thống AI
thực tế, vector store là thành phần cốt lõi của semantic search, hệ gợi ý, gom
cụm, và đặc biệt là retrieval-augmented generation. Thay vì so khớp từ khóa, nó
so khớp theo khoảng cách hình học giữa các vector trong không gian nhiều chiều.

## Cách hoạt động

Khi nạp tài liệu, hệ thống chia văn bản thành các chunk, tạo embedding cho từng
chunk, rồi lưu kèm metadata. Khi người dùng đặt câu hỏi, hệ thống tạo embedding
cho câu hỏi đó và so sánh với toàn bộ vector đã lưu để tìm ra các chunk gần nhất
theo cosine similarity. Kết quả top-k được trả về cùng điểm số, giúp người dùng
biết mức độ liên quan của từng kết quả.

## Lưu trữ kèm metadata

Mỗi chunk nên được lưu cùng metadata mô tả nó, ví dụ nguồn tài liệu, ngôn ngữ,
chủ đề, hoặc mã định danh chunk. Metadata cho phép lọc trước khi tìm kiếm: ta có
thể chỉ tìm trong các tài liệu tiếng Việt, hoặc chỉ trong một chủ đề cụ thể. Việc
lọc trước thu hẹp tập ứng viên, vừa giảm nhiễu vừa tăng tốc độ truy vấn.

## Các thao tác cơ bản

Một vector store tối thiểu cần hỗ trợ bốn thao tác. Thêm tài liệu để nạp và embed
chunk mới. Tìm kiếm để xếp hạng chunk theo độ tương đồng với câu hỏi. Lọc theo
metadata để giới hạn phạm vi tìm kiếm. Và xóa tài liệu để gỡ bỏ mọi chunk thuộc
một tài liệu khi nội dung đã lỗi thời. Bốn thao tác này đủ để xây một trợ lý tri
thức nội bộ hoàn chỉnh.

## Khi nào cần vector store chuyên dụng

Với vài nghìn chunk, một kho trong bộ nhớ đơn giản đã đủ nhanh và dễ kiểm thử.
Khi dữ liệu lớn lên hàng triệu vector, ta cần các giải pháp chuyên dụng như
Chroma, FAISS hay các cơ sở dữ liệu vector có lập chỉ mục xấp xỉ để giữ tốc độ.
Tuy nhiên, nguyên lý cốt lõi không đổi: embed, lưu, rồi xếp hạng theo độ tương
đồng.
