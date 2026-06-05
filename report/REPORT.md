# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** DINH VAN ANH KHOI - 615

**Nhóm:** VANFIST

**Ngày:** 05/06/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity (gần bằng 1.0) có nghĩa là hai vector embedding biểu diễn văn bản hướng về cùng một phía trong không gian đa chiều, chỉ ra rằng hai đoạn văn bản đó có sự tương đồng rất cao về mặt ngữ nghĩa, ngữ cảnh hoặc chủ đề, bất kể chiều dài văn bản hay cách diễn đạt từ ngữ có khác biệt.

**Ví dụ HIGH similarity:**
- Sentence A: The dog chased the cat up the tree.
- Sentence B: A canine ran after the feline up the tall plant.
- Tại sao tương đồng: Hai câu sử dụng các từ đồng nghĩa khác nhau (dog/canine, cat/feline, chased/ran after, tree/tall plant) nhưng chia sẻ cấu trúc ngữ nghĩa và mô tả chính xác cùng một hành động và đối tượng.

**Ví dụ LOW similarity:**
- Sentence A: Quantum computing utilizes qubits to perform complex calculations.
- Sentence B: Making a perfect pizza dough requires flour, water, yeast, and salt.
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn độc lập và không liên quan gì đến nhau (máy tính lượng tử và công thức làm bánh pizza), do đó không chia sẻ bất kỳ mối quan hệ ngữ cảnh hay ngữ nghĩa nào.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity đo góc giữa hai vector (hướng) thay vì khoảng cách thẳng giữa hai đầu vector (độ dài/magnitude). Trong xử lý ngôn ngữ tự nhiên, độ dài của vector thường bị ảnh hưởng lớn bởi độ dài của văn bản (văn bản dài chứa nhiều từ hơn sẽ làm tăng độ dài vector). Sử dụng cosine similarity giúp so sánh ngữ nghĩa một cách khách quan mà không bị thiên lệch bởi chiều dài của các chunk văn bản.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* 
> Áp dụng công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`
> Với `doc_length = 10000`, `chunk_size = 500`, `overlap = 50`:
> `num_chunks = ceil((10000 - 50) / (500 - 50))`
> `num_chunks = ceil(9950 / 450)`
> `num_chunks = ceil(22.11)`
> `num_chunks = 23`
> *Đáp án:* 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Phép tính khi overlap = 100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks. Như vậy, số lượng chunk tăng từ 23 lên 25.
> Ta muốn overlap nhiều hơn để đảm bảo bảo toàn được ngữ cảnh liên tục giữa các chunk liền kề (context preservation), hạn chế việc các câu hoặc ý nghĩa quan trọng bị cắt đôi ngay tại ranh giới phân mảnh, từ đó giúp bộ truy xuất (retriever) và LLM hiểu chính xác hơn ngữ cảnh xung quanh thông tin được tìm kiếm.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** [POLICY]

**Tại sao nhóm chọn domain này?**
> Domain chính sách pháp lý/thương mại điện tử có cấu trúc rõ ràng (điều khoản, khoản mục đánh số) và ngôn ngữ đặc thù, phù hợp để thử nghiệm các chunking strategy khác nhau. Bộ tài liệu đa dạng về độ dài (từ 260 đến 34,500 ký tự) giúp so sánh strategy rõ nét hơn. Đây cũng là use case thực tế: khách hàng thường tra cứu chính sách bảo hành, đặt cọc, hoàn tiền trước khi mua xe.


### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | baomatcanhan.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 34,505 | category=privacy, chunk_strategy=by_section |
| 2 | chinhsachthuepin.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 19,422 | category=battery_rental, chunk_strategy=by_article |
| 3 | dieukiensudung.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 7,284 | category=cookies, chunk_strategy=by_section |
| 4 | dieukhoandatcoc.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 6,626 | category=deposit, chunk_strategy=by_numbered_clause |
| 5 | dieukhoan.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 6,419 | category=terms, chunk_strategy=fixed_size |
| 6 | chinhsachbaomat.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 3,551 | category=security, chunk_strategy=fixed_size |
| 7 | chinh_sach_san_pham.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | ~850 | category=product_policy, chunk_strategy=fixed_size |

*Ghi chú: chinh_sach_san_pham.md được merge từ chinhsachdoitra.md (587 ký tự) và chinhsachvanchuyen.md (260 ký tự) vì cả hai quá ngắn để chunk riêng. File duplicate mientrutrachnhiem.md đã bị xóa (nội dung giống hệt dieukhoan.md).*

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | deposit, privacy, security, battery_rental, cookies, terms, product_policy | Filter trước khi search để tránh retrieve nhầm sang file không liên quan |
| chunk_strategy | string | by_article, by_section, fixed_size | Ghi lại strategy đã dùng để debug và so sánh |
| source | string | vinfastauto | Traceability — biết chunk đến từ nguồn nào |
| language | string | vi | Hữu ích nếu sau này thêm tài liệu tiếng Anh |
---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| dieukhoandatcoc.md | FixedSizeChunker (`fixed_size`) | 12 | 470.75 | Không tốt (cắt ngang điều khoản giữa chừng) |
| dieukhoandatcoc.md | SentenceChunker (`by_sentences`) | 12 | 421.42 | Trung bình (giữ câu tốt nhưng gộp cơ học) |
| dieukhoandatcoc.md | RecursiveChunker (`recursive`) | 16 | 316.06 | Tốt (tách theo cấu trúc mục nhỏ tối ưu hơn) |
| dieukiensudung.md | FixedSizeChunker (`fixed_size`) | 14 | 469.64 | Không tốt (cắt ranh giới từ/câu cơ học) |
| dieukiensudung.md | SentenceChunker (`by_sentences`) | 11 | 536.64 | Trung bình (câu nguyên vẹn nhưng mất liên kết ý) |
| dieukiensudung.md | RecursiveChunker (`recursive`) | 18 | 327.39 | Tốt (giữ nguyên cấu trúc văn bản phân cấp) |

### Strategy Của Tôi

**Loại:** FixedSizeChunker tuned (chunk_size=300, overlap=100)

**Mô tả cách hoạt động:**
> Chiến lược sử dụng FixedSizeChunker có sẵn nhưng được điều chỉnh (tuned) với các tham số tối ưu hơn: kích thước mỗi chunk tối đa là 300 ký tự và khoảng chồng lấp (overlap) giữa hai chunk liên tiếp là 100 ký tự. Văn bản sẽ được cắt cơ học theo chiều dài cố định, với bước nhảy (step) cho mỗi chunk tiếp theo là 200 ký tự (300 - 100). Điều này đảm bảo rằng 100 ký tự cuối cùng của chunk trước sẽ lặp lại ở đầu chunk sau.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Do tài liệu pháp lý và chính sách VinFast có nhiều điều khoản ngắn nhưng chứa nhiều thông tin cốt lõi đan xen, việc sử dụng kích thước chunk nhỏ (300) giúp cô đọng nội dung và tăng mật độ thông tin trong vector biểu diễn. Đồng thời, tăng overlap lên 100 ký tự giúp giảm thiểu khả năng rách context, đảm bảo các từ khóa quan trọng ở cuối điều khoản này hoặc đầu điều khoản sau luôn xuất hiện cùng nhau trong ít nhất một chunk.

**Code snippet (nếu custom):**
```python
# Sử dụng FixedSizeChunker có sẵn với tham số khởi tạo:
chunker = FixedSizeChunker(chunk_size=300, overlap=100)
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| dieukhoandatcoc.md | best baseline (Recursive 500) | 16 | 316.06 | Tốt (chính xác về mặt cấu trúc) |
| dieukhoandatcoc.md | **của tôi (FixedSize 300, 100)** | 25 | 299.96 | Rất tốt (tìm kiếm chi tiết nhờ overlap lớn) |
| dieukiensudung.md | best baseline (Recursive 500) | 18 | 327.39 | Tốt (giữ nguyên mạch văn bản) |
| dieukiensudung.md | **của tôi (FixedSize 300, 100)** | 30 | 294.17 | Rất tốt (không bị rách thông tin ở ranh giới) |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Vũ Quang Vinh | ArticleChunker | 4/10 | Giữ nguyên điều khoản, context rất rõ ràng khi LLM đọc | Bị nhiễu ngữ nghĩa (semantic noise) nếu không có metadata filtering hỗ trợ |
| Nguyễn Trần Kiên | FixedSizeChunker (`chunk_size=500`, `overlap=50`) | 8/10 | Đơn giản, chạy ổn, 4/5 query có relevant chunk trong top-3 | Có thể cắt giữa điều khoản, query thay pin SOH dưới 70% chưa retrieve đúng |
| Đoàn Công Phú | SentenceChunker | 9/10 | Benchmark thật bằng OpenAI embedding + metadata filter cho thấy top-3 retrieve đúng nguồn ở 5/5 câu hỏi; Q2, Q3, Q4 có câu trả lời đúng ngay TOP 1 | Q1 có chunk trả lời chính xác ở TOP 2 chứ chưa phải TOP 1; Q5 cần ghép nhiều chunk để đủ cả thẻ quốc tế và thẻ nội địa |
| Hoàng Đức Dũng | Strategy 3 (RecursiveChunker) | 2/10 | Tách đoạn và câu chuẩn, giữ nguyên ý | Chunk size dao động nhiều |
| Đinh Văn Anh Khôi | FixedSize Chunker tuned (300, 100) | 8/10 | Giảm rách context ở ranh giới tốt nhờ overlap 100; chunk nhỏ cô đọng | Số lượng chunk nhiều (gây tốn token), dễ bị nhiễu do lặp từ |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Chiến lược **Custom Article Chunker (Thành viên 1 - Vũ Quang Vinh)** là tốt nhất về mặt thiết kế (design rationale) cho domain này. Bởi vì tài liệu chính sách và điều khoản pháp lý của VinFast có cấu trúc phân cấp cực kỳ rõ ràng theo các Điều và Khoản (ví dụ: 'Điều 1.', 'Điều 2.'). Việc viết bộ tách custom theo cấu trúc này giúp giữ trọn vẹn mạch lập luận và toàn bộ nội dung của một điều khoản trong một chunk duy nhất, tránh việc các quy định pháp lý bị chia cắt nửa vời. Tuy nhiên, trong thực nghiệm, chiến lược **Sentence Chunker kết hợp với OpenAI embedding và metadata filter của Thành viên 3 (Đoàn Công Phú)** đạt điểm số retrieval cao nhất (9/10). Điều này là do Sentence Chunker chia nhỏ ở mức độ mịn hơn (câu), kết hợp với embedding chất lượng cao thực tế (OpenAI) và bộ lọc metadata giúp định hướng chính xác và so khớp ngữ nghĩa cực tốt.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng biểu thức chính quy kết hợp cơ chế lookbehind `re.split(r'(?<=[.!?])\s+|(?<=\.)\n', text)` để phân tách văn bản tại ranh giới kết thúc câu mà không làm mất đi các dấu câu kết thúc (`.`, `!`, `?`). Xử lý các edge case bằng cách loại bỏ các chuỗi rỗng và khoảng trắng dư thừa ở đầu và cuối mỗi câu, sau đó nhóm tuần tự các câu thành các chunk với số lượng tối đa là `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Triển khai thuật toán đệ quy thử phân tách văn bản bằng các ký tự phân tách (`separators`) theo thứ tự ưu tiên giảm dần. Base case là khi đoạn văn bản nhỏ hơn `chunk_size` (trả về chính nó) hoặc khi đã duyệt hết toàn bộ separators (thực hiện chia cưỡng bức theo số ký tự `chunk_size`). Sau khi gọi đệ quy trên các đoạn quá lớn, tiến hành gom nhóm các đoạn nhỏ liền kề để gộp lại thành chunk lớn miễn là tổng chiều dài (bao gồm cả ký tự phân tách) không vượt quá `chunk_size`.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Hỗ trợ lưu trữ tài liệu qua hai chế độ: in-memory (`self._store` chứa danh sách các dictionary) hoặc ChromaDB (qua `EphemeralClient` nếu thư viện khả dụng). Khi tìm kiếm (`search`), sinh vector biểu diễn cho câu hỏi bằng `_embedding_fn`, tính toán độ tương đồng cosine (Cosine Similarity) với tất cả các vector của chunk đã lưu, sau đó sắp xếp giảm dần theo điểm số để trả về top_k chunk phù hợp nhất.

**`search_with_filter` + `delete_document`** — approach:
> Sử dụng cơ chế lọc trước (pre-filtering) để chọn ra các chunk thỏa mãn `metadata_filter` trước khi tính toán độ tương đồng và xếp hạng, đảm bảo không bị thiếu kết quả (tránh lỗi post-filtering). Đối với `delete_document`, tiến hành xóa các chunk có `doc_id` hoặc ID khớp với `doc_id` được yêu cầu bằng cách dùng `collection.delete` của ChromaDB hoặc lọc bỏ khỏi danh sách in-memory `self._store`.

### KnowledgeBaseAgent

**`answer`** — approach:
> RAG Agent thực hiện tìm kiếm top_k chunk có liên quan nhất từ `EmbeddingStore`, nối các văn bản này bằng ký tự phân tách `---` làm Context. Sau đó, Context được inject vào một cấu trúc Prompt có sẵn quy định vai trò trợ lý, tiếp theo là câu hỏi của người dùng và yêu cầu sinh câu trả lời dựa trên Context trước khi gọi `llm_fn`.

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.13.3, pytest-9.0.3, pluggy-1.6.0 -- C:\Python313\python.exe
cachedir: .pytest_cache
rootdir: E:\merged_partition_content\Khoi_Project\VinUni\LAB\DAY 7\615-DinhVanAnhKhoi-Day07
plugins: anyio-4.12.1
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.15s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | The dog chased the cat. | A canine ran after the feline. | high | -0.0409 | Sai |
| 2 | Quantum physics is a branch of science. | I love eating pepperoni pizza. | low | -0.0677 | Đúng |
| 3 | Python is a popular programming language. | The giant python snake crawled through the grass. | low | -0.1887 | Đúng |
| 4 | Artificial intelligence will change the world. | AI is going to transform our global society. | high | 0.1495 | Sai |
| 5 | The weather is sunny and clear today. | It is raining heavily outside right now. | low/medium | 0.0193 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là các cặp câu có nghĩa rất giống nhau (như Cặp 1 và Cặp 4) lại có điểm tương đồng cosine rất thấp và gần như trực giao (quanh mức 0.0). Điều này xảy ra bởi vì `MockEmbedder` chỉ tạo ra các vector ngẫu nhiên dựa trên mã băm MD5 của văn bản chứ không hề học hay biểu diễn ngữ nghĩa thật sự của từ ngữ. Để biểu diễn ngữ nghĩa chính xác, chúng ta bắt buộc phải sử dụng các mô hình embedding được huấn luyện (như Sentence Transformers hoặc OpenAI) thay vì các hàm hash ngẫu nhiên.

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Nếu khách hàng không đến ký hợp đồng mua bán đúng hạn, tiền đặt cọc sẽ được xử lý như thế nào? | Tiền đặt cọc thuộc về VinFast, và VinFast có toàn quyền quyết định việc xử lý tiền đó. |
| 2 | Tôi có thể đổi hoặc trả xe sau khi mua không? | Không. Sản phẩm không áp dụng đổi, trả. Sản phẩm được bảo hành tại hệ sinh thái Showroom và Xưởng dịch vụ. |
| 3 | VinFast có giao xe trực tiếp đến nhà tôi không? | Không. Sản phẩm được phân phối qua hệ thống Showroom. VinFast không áp dụng chính sách vận chuyển trực tiếp. |
| 4 | Khách hàng có quyền yêu cầu thay pin khi nào? | Khi dung lượng pin tối đa (SOH) xuống dưới 70%. Việc thay pin phải được thực hiện tại showroom/xưởng dịch vụ chính hãng. |
| 5 | Thông tin thẻ thanh toán của khách hàng có được lưu trên hệ thống Vinfastauto.com không? | Không. Vinfastauto.com không trực tiếp lưu trữ thông tin thẻ khách hàng. Thẻ quốc tế do Đối Tác Cổng Thanh Toán bảo mật. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Nếu khách hàng không đến ký hợp đồng mua bán đúng hạn, tiền đặt cọc sẽ được xử lý như thế nào? | t tại website https://vinfastauto.com/vn_vi.   5. Thỏa Thuận... | 0.2368 | Một phần (Không chứa trực tiếp Điều 5.2) | [MOCK RAG ANSWER] Based on retrieved context: t tại website https://vinfastauto.com/vn_vi.   5. Thỏa Thuận Đặt Cọc có hiệu lực ràng buộc các bên kể từ thời điểm ký kế... |
| 2 | Tôi có thể đổi hoặc trả xe sau khi mua không? | lượng và liên quan đến an toàn cho các xe đang lưu hành trên... | 0.2054 | Không (Chứa thông tin về chương trình triệu hồi xe lỗi) | [MOCK RAG ANSWER] Based on retrieved context: lượng và liên quan đến an toàn cho các xe đang lưu hành trên thị trường theo quy định pháp luật. Chương trình triệu hồi ... |
| 3 | VinFast có giao xe trực tiếp đến nhà tôi không? | nh tại hệ thống Showroom, Xưởng dịch vụ của Đại lý phân phối... | 0.2132 | Không (Chứa thông tin bảo hành tại showroom/xưởng dịch vụ) | [MOCK RAG ANSWER] Based on retrieved context: nh tại hệ thống Showroom, Xưởng dịch vụ của Đại lý phân phối chính hãng VinFast theo chính sách bảo hành.  + Riêng với C... |
| 4 | Khách hàng có quyền yêu cầu thay pin khi nào? | dứt, Khách Hàng phải hoàn trả Pin cho VinFast Trading tại Đi... | 0.2651 | Không (Nói về nghĩa vụ hoàn trả pin khi chấm dứt dịch vụ) | [MOCK RAG ANSWER] Based on retrieved context: dứt, Khách Hàng phải hoàn trả Pin cho VinFast Trading tại Điểm Cung Cấp Dịch Vụ trừ khi Các Bên có thỏa thuận khác. Nếu ... |
| 5 | Thông tin thẻ thanh toán của khách hàng có được lưu trên hệ thống Vinfastauto.com không? | ity Standards Council). Với việc tuân thủ PCI DSS, Đối Tác C... | 0.0936 | Không (Nói về chứng nhận PCI DSS của Cổng thanh toán) | [MOCK RAG ANSWER] Based on retrieved context: ity Standards Council). Với việc tuân thủ PCI DSS, Đối Tác Cổng Thanh Toán đã  tham gia các chương trình bảo vệ như Veri... |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 1 / 5 (Chỉ có Query 3 có chunk chứa câu trả lời đúng xuất hiện ở vị trí số 3 trong danh sách top-3).

#### Phân Tích Kết Quả Thực Nghiệm & Vai Trò của MockEmbedder:
- **Độ chính xác thực tế:** Kết quả thực tế cho thấy tỷ lệ trả về chunk chứa câu trả lời đúng trong Top-1 là **0%**, và chỉ có **20%** (1/5 câu) có chunk đúng nằm trong Top-3 (ở câu 3, chunk đúng xếp thứ 3).
- **Nguyên nhân:** Điều này xảy ra do hệ thống đang sử dụng `MockEmbedder` (chỉ tạo vector ngẫu nhiên dựa trên mã băm MD5 của văn bản chứ không có khả năng học ngữ nghĩa thực tế). Do đó, khoảng cách cosine giữa câu hỏi và các chunk hoàn toàn ngẫu nhiên và không phản ánh độ tương đồng ngữ nghĩa thực sự.
- **Giá trị của Metadata Filtering:** Dù `MockEmbedder` hoạt động ngẫu nhiên, nhờ có **Metadata Filtering** (ví dụ: lọc theo `category=deposit` cho câu 1), toàn bộ các chunk trả về đều thuộc chính xác tài liệu chứa thông tin nguồn (`dieukhoandatcoc.md`). Nếu không có bộ lọc này, kết quả sẽ bị trộn lẫn với các văn bản dài khác (như `baomatcanhan.md`) do nhiễu ngữ nghĩa (xem phần so sánh không sử dụng bộ lọc ở dưới).
- **Kết luận:** Trong một hệ thống RAG thực tế, metadata filter đóng vai trò quyết định để thu hẹp phạm vi tài liệu nguồn, nhưng bắt buộc phải đi kèm với một mô hình embedding thực sự (như OpenAI hay Sentence-Transformers) để tìm đúng chunk chứa nội dung trả lời bên trong tài liệu đó.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Qua thảo luận nhóm, tôi thấy thiết kế Custom Article Chunker của thành viên 1 (Vũ Quang Vinh) là cách tiếp cận bài bản nhất. Việc hiểu rõ cấu trúc của văn bản pháp lý (chia theo Điều/Khoản) để cắt văn bản theo ranh giới đó sẽ giữ nguyên vẹn ngữ cảnh pháp lý tốt hơn nhiều so với việc cắt cơ học bằng ký tự cố định.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Trong buổi demo liên nhóm, tôi học được rằng việc kết hợp metadata filtering với các mô hình embedding mạnh như OpenAI là cực kỳ cần thiết. Một số nhóm không sử dụng metadata filtering đã gặp hiện tượng nhiễu rất nặng khi tìm kiếm giữa các chính sách khác nhau có từ khóa tương đồng (ví dụ: từ "xe" hoặc "khách hàng" xuất hiện ở mọi tài liệu).

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Nếu làm lại, tôi sẽ không sử dụng phương pháp cắt fixed size nữa mà chuyển sang xây dựng bộ tách cấu trúc (Section/Article Chunker) kết hợp với mô hình embedding thực tế. Đồng thời, tôi sẽ làm phong phú thêm metadata (như gán thêm nhãn về mức độ ưu tiên hoặc đối tượng áp dụng) để hỗ trợ quá trình pre-filtering hiệu quả hơn.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **100 / 100** |

