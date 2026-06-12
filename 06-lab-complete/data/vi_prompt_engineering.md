# Kỹ Thuật Viết Prompt Cho RAG

## Vì sao prompt quan trọng

Trong hệ thống RAG, mô hình ngôn ngữ không bao giờ nhìn thấy cơ sở dữ liệu gốc.
Nó chỉ thấy prompt mà ta dựng nên, gồm các chunk đã truy xuất cùng với chỉ thị
của ta. Một prompt tốt biến context liên quan thành câu trả lời có căn cứ; một
prompt cẩu thả khiến mô hình bỏ qua context và bịa thông tin. Vì vậy prompt là
cây cầu nối giữa chất lượng retrieval và chất lượng câu trả lời.

## Cấu trúc một prompt RAG

Một prompt RAG đáng tin cậy có ba phần. Phần đầu là chỉ thị, yêu cầu mô hình chỉ
trả lời dựa trên context và thừa nhận khi không biết. Phần giữa là khối context,
trong đó mỗi chunk được đánh số để mô hình có thể trích dẫn. Phần cuối là câu hỏi
của người dùng, đặt sau cùng để nó còn rõ trong sự chú ý của mô hình. Giữ thứ tự
này ổn định giúp câu trả lời nhất quán hơn.

## Grounding và trích dẫn

Grounding nghĩa là câu trả lời được hỗ trợ bởi văn bản đã truy xuất chứ không
phải trí nhớ của mô hình. Để khuyến khích grounding, hãy ra chỉ thị rõ ràng như
"chỉ trả lời dựa trên context bên dưới". Việc đánh số chunk thành [1], [2], [3]
cho phép mô hình chỉ ra nguồn, khiến câu trả lời có thể kiểm chứng. Nếu không có
chunk nào liên quan, hệ thống nên trả về thông báo dự phòng thay vì đoán.

## Những lỗi thường gặp

Một số lỗi âm thầm làm giảm chất lượng câu trả lời RAG. Nhồi quá nhiều chunk vào
prompt làm loãng những chunk hữu ích và tăng chi phí. Quên chỉ thị "chỉ dùng
context" mở đường cho việc bịa thông tin. Đặt câu hỏi trước một khối context dài
khiến mô hình quên mất câu hỏi. Và không xử lý trường hợp truy xuất rỗng khiến mô
hình tạo ra câu trả lời khi lẽ ra phải thừa nhận không chắc chắn.

## Lặp lại và tinh chỉnh

Hãy coi prompt là thứ cần thử nghiệm, không phải viết một lần là xong. Chạy bộ
câu hỏi benchmark, đọc câu trả lời, và tìm những trường hợp mô hình bỏ qua context
hoặc thêm thông tin không có thật. Những thay đổi nhỏ trong cách diễn đạt, như
thêm "hãy ngắn gọn" hoặc "trích câu liên quan", thường cải thiện grounding nhiều
hơn là đổi sang một mô hình lớn hơn.
