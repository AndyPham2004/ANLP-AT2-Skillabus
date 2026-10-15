# Kế hoạch 14/10/2026: dữ liệu gọn một chỗ, đủ cho toàn ngành IT

Claude soạn cho Quan, tối 14/10, cập nhật sáng 15/10. **Chỉ là kế hoạch, chưa dời file, chưa chạy gì.** Quan dừng việc thực hiện
để hiểu hết dữ liệu trước. Số đếm đọc từ `origin/main` (commit 72e417a) và dữ liệu thô trên máy Quan.
Hạn nộp 17/10.

Ba mục tiêu:

1. **Gọn:** mọi dữ liệu nằm trong **một** thư mục `data/`, chia theo cách dùng. Thư mục code không chứa dữ liệu.
2. **Một nguồn cho mỗi thứ:** một bộ từ vựng kỹ năng, một bảng nhu cầu. Không còn hai từ điển, sáu file nhu cầu.
3. **Toàn ngành IT:** mọi dữ liệu nhu cầu có cho từng vai trò, không chỉ Data Scientist.

## Phiên tiếp theo: bắt đầu từ đây

Ghi lúc 00:31 ngày 15/10. Máy Quan đang ở nhánh `qp/data-layout` (= `origin/main` cộng file này và dòng `.ua/` trong
`.gitignore`, cả hai chưa commit). Chưa dời file nào, chưa xoá nhánh nào.

**Quan đã đồng ý (15/10, 00:30):**

1. Claude review 14 nhánh chưa merge (mục 6, Bước 0) và đăng nhận xét lên GitHub, ký `_Reviewed with Claude Code on
   Quan's behalf._`. Cách review: trial-merge từng PR lên `main` trong worktree riêng, chạy toàn bộ pytest, kiểm lại
   các con số PR tuyên bố; có thể chia agent theo người. PR của Quan (#80, #94, #98) không tự duyệt được: nhờ Văn Thông.
2. Báo nhóm mốc đóng băng 12:00 ngày 15/10. Tin nhắn soạn sẵn ở Phụ lục A.

**Chưa được đồng ý, phải hỏi Quan trước:** xoá nhánh trên GitHub; xoá rác trên máy; bắt đầu PR dọn thư mục (Quan bảo
khi Bước 0 xong).

**Bước 0:** đợt review 1 xong 01:25 ngày 15/10 (trial-merge từng PR lên `main`, chạy toàn bộ pytest, kiểm lại số); báo nhóm qua issue #100. Cập nhật 09:30: Văn Thông duyệt #98, #94, #80 đêm 14/10; Claude merge #98, #94, #97. `main` = 0c54d11, 154 test. 11:50: không ai push thêm; #82, #83, #54, #56, #88, #89, #91 rebase sau PR dọn thư mục. Quan chốt 09:35: PR dọn thư mục chạy 12:00; xoá nhánh đã merge lúc 14:00. Ghi chú trên #97 nhờ Văn Thông sửa 3 câu ở chương 03 nói quá so với code.

| PR | Nhánh | Kết quả đêm 15/10 | Đang chờ |
|---|---|---|---|
| #99 | `vt/ats-rerun` | APPROVED, **đã merge** (a367a11) | Xoá nhánh khi Quan đồng ý |
| #98 | `qp/antirequisite-fix` | Văn Thông duyệt (tải lại 172 trang, 0 khác biệt); **đã merge** (1ac7a7e) | Sau đóng băng: 3 môn có điều kiện parser bỏ sót (421028, 31030, 94689; xem review của Văn Thông) |
| #94 | `qp/review-followups` | Văn Thông duyệt; **đã merge** (b70ed13). Gồm sửa `.gitignore` và lỗi không có khoá | — |
| #82 | `pn/prerequisites` | COMMENT: code đúng trên dữ liệu #98; còn test hồi quy, fixture cũ, 1 dòng contract. 09:25 đã nhắc: #98 vào rồi | Phương Nhi |
| #83 | `pn/two-tier` (draft) | COMMENT: không có lỗi chặn, sẽ duyệt khi ready; 5 chỗ còn giả định Data Scientist (cho C2) | #82 merge |
| #54 | `ht/eval-fixes` | Hướng dẫn gỡ xung đột 1 dòng; **phải merge trước #56** (`restrict_to`) | Hoài Thương |
| #56 | `ht/eval-run` + `ht/eval-subjects-chat` | CHANGES_REQUESTED: tier 3 chấm không qua `normalise()` (F1 0,456 → 0,585); số chương 6 lệch vì `main` đã đổi; P@3 môn = 1 do thiếu cặp âm, 29 tên môn trùng mã | Hoài Thương |
| #97 | `vt/report-03` | Văn Thông sửa đủ (61f532a); duyệt, **đã merge** (0c54d11) | Văn Thông: `03_data.md:117` đổi 2.208 → 2.200 requisite, thêm 301 anti-requisite / 172 môn (PR docs) |
| — | `vt/external-check` | Commit đã vào `main` cùng #97 | — |
| #88, #89, #91 | `ak/*` | Akash sửa 15/10 09:42; review lại 10:05: CHANGES_REQUESTED (#88 6 điểm, #89 5 điểm, #91 3 dòng); hai lỗi do câu chữ trong review cũ của Quan (luật merge; định nghĩa kỹ năng mới nổi), đã đính chính | Akash; rebase sau 14:00 (chỉ đổi đường dẫn trong chữ) |
| #80 | `qp/ideas` | Sửa theo 4 góp ý của Văn Thông, thêm dòng "đã cũ"; **đã merge** (fcdd366) | — |

Cho PR dọn thư mục: cache đánh giá GPT (`data/cache/llm_extract/`, 30 file đã commit) cần chỗ trên git, vì `runtime/`
không lên git; test hồi quy của #82 đọc `data/processed/` trực tiếp, đổi sang `paths.py`.

## 0. Quyết định của Quan (14/10)

| # | Câu hỏi | Quan chốt |
|---|---|---|
| 1 | Danh sách vai trò | 7 vai trò có số liệu Úc **cộng** Cybersecurity, Network/Systems Administrator, QA/Test Engineer, DevOps/SRE |
| 2 | Vai trò không có số liệu Úc | App hiện **"kỹ năng cốt lõi"**, không vẽ phần trăm |
| 3 | Khi nào dời thư mục | Dời ngay; tạm dừng tối 14/10 để Quan hiểu dữ liệu trước, làm khi Quan bảo |
| 4 | Tên thư mục | Có số thứ tự (`1_knowledge/`) |
| 5 | Ai làm PR dời thư mục | Quan (Claude làm trên nhánh `qp/data-layout` của Quan) |
| 6 | Từ điển và ESCO | Gộp thành **một** bộ từ vựng: ESCO làm nền, nhóm thêm phần ESCO thiếu (mục 3) |
| 7 | Khoá học ngoài | Thành **kho tự học sâu và rộng** kèm chứng chỉ "hot" đo được (D9, D11), vì IT là ngành phải tự học suốt |
| 8 | Môn UTS quá nông | Ghi kỹ năng môn thật sự dạy qua Canvas của chính sinh viên, chỉ ghi tên kỹ năng (D10) |
| 9 | Nhu cầu thị trường cũ, ít mẫu | Nâng chất lượng bằng D12–D15: đếm Adzuna, số liệu chính phủ, bắt buộc / lợi thế, so cùng vai trò |
| 10 | File nhiễu, đồ cũ | **Chuyển vào archive, không xoá.** Thư mục `poster/` của AT2A cũng vào archive. Mọi đồ cũ gom vào **một** thư mục `archive/` ở gốc repo |

---

## 1. Hiện trạng: dữ liệu đang nằm ở 10 chỗ

| Chỗ | File | Có gì |
|---|---|---|
| `data/processed/` | 18 | Từ điển, liên kết ESCO, hồ sơ môn, tiên quyết, kỳ mở, khoá ngoài, 6 bảng nhu cầu, `gap.csv` poster |
| `data/labels/` | 10 | 4 file nhãn, 5 mẫu trống, README |
| `data-eda/data/clean/` | 8 | Tin đã làm sạch, ESCO đã làm sạch, mẫu 200 tin, CV đã che tên |
| `data-eda/outputs/` | 19 | Kết quả EDA và poster: số đếm, LinkedIn Mỹ, Glassdoor, hình |
| `data-eda/config/` | 5 | **Từ điển gốc 133 dòng**, nguồn liên kết ESCO, danh sách công ty ATS |
| `app/mock/` | 7 | JD và CV mẫu; mock cũ 70 môn |
| `data/raw/data-eda/`, `data-eda/data/raw/` | | Hai bản tải về, không trên git |
| `data/cache/`, `models/` | | Cache GPT, Lightcast, vector; không trên git |

Ba chỗ rối nhất: hai từ điển (133 dòng ở `config`, 148 dòng ở `processed`); một loại dữ liệu rải nhiều chỗ
(ESCO sạch ở `data-eda`, liên kết ESCO ở `data/processed`); tên file không nói công dụng (`gap.csv`, `top_skills.csv`).

---

## 2. Sau khi dọn: một thư mục `data/`

```text
data/
├── README.md                          bản đồ: mỗi file một dòng, dùng làm gì, ai tạo, lệnh tạo lại
│
├── 1_knowledge/                       KHO TRI THỨC: app tra cứu khi chạy
│   ├── skills/skills_vocabulary.csv   MỘT bộ từ vựng kỹ năng (thay từ điển + liên kết ESCO, mục 3)
│   ├── taxonomies/                    ESCO đầy đủ (bảng tra), kỹ năng theo nghề của ESCO và O*NET
│   ├── uts/                           hồ sơ môn, tiên quyết, kỳ mở, assessment
│   └── learning_resources/            tự học ngoài UTS: khoá học, tài liệu chính thức, lab, chứng chỉ
│
├── 2_demand/                          NHU CẦU THỊ TRƯỜNG: theo từng vai trò
│   ├── roles.csv                      danh sách vai trò, nhóm ngành, mẫu chức danh, mã ESCO/O*NET, nguồn ưu tiên
│   ├── role_skill_demand.csv          MỘT bảng: vai trò × kỹ năng × nguồn × giai đoạn
│   ├── ads/                           tin tuyển dụng toàn văn đã làm sạch, một file mỗi nguồn
│   ├── collection/                    danh sách công ty ATS, nhật ký dò board
│   └── emerging/                      kỹ năng mới nổi
│
├── 3_tuning/                          CHỈNH THAM SỐ: README ghi ngưỡng nào chỉnh trên dữ liệu nào
│
├── 4_evaluation/                      ĐÁNH GIÁ
│   ├── labels/                        4 file nhãn + mẫu trống
│   ├── inputs/                        mẫu 200 tin để gắn nhãn, CV đã che tên
│   └── results/                       bảng điểm cho chương 6
│
├── 5_crosscheck/                      KIỂM CHÉO: LinkedIn Mỹ, Glassdoor, so Úc-Mỹ, độ phủ ESCO
│
├── raw/                               (không lên git) MỘT chỗ cho mọi bản tải về
└── runtime/                           (không lên git) vote, cache GPT, cache Lightcast, chỉ mục vector
```

Toàn repo sau khi dọn: mở ra chỉ thấy những thứ đang dùng, đồ cũ nằm gọn trong `archive/`.

```text
at2/
├── app/            app Streamlit (chỉ code + JD và CV mẫu)
├── src/skillabus/  pipeline NLP (chỉ code; paths.py khai báo mọi đường dẫn)
├── tests/          test
├── data/           dữ liệu đang dùng, năm mục theo cách dùng (cây ở trên)
├── data-eda/       script thu và làm sạch dữ liệu của Văn Thông (chỉ code)
├── notebooks/      notebook khám phá
├── docs/           báo cáo, data contract, deploy, wireframe; docs/notes/ cho ghi chú làm việc
└── archive/        ĐỒ CŨ, ĐÓNG BĂNG, không ai sửa
    ├── README.md            mỗi thư mục con một dòng: là gì, vì sao giữ
    ├── poster_AT2A/
    │   ├── poster/          AT2A_Poster_Skillabus.html, _A0.pdf, _preview.png, figures/uts_logo.png
    │   ├── tools/           export_poster.py, make_qr.py
    │   ├── data/            gap.csv, skill_counts.csv, skill_counts_wide.csv, ad_skill_long.csv, BLOCKS_B.md, FOR_A_blocks_3_and_5.md, 2 hình block
    │   ├── scripts/         extract_skills.py, chart_sources.py, chart_top15.py, source_counts.py
    │   └── handoffs/        bàn giao của Văn Thông, Phương Nhi, Hoài Thương cho poster (8 file)
    ├── mock_2026-10-03/     subject_layers.csv, gap_job_seeker.json, gap_role_data_scientist.json, build_mock.py
    ├── dictionary_v1/       từ điển gốc 133 dòng, liên kết ESCO gốc (sau khi có bộ từ vựng)
    └── demand_files_v1/     skill_counts_v2, skill_counts_2026, top_skills, role_profiles (sau khi gộp bảng nhu cầu)
```

Poster trong `archive/poster_AT2A/poster/` giữ nguyên cấu trúc thư mục con, nên vẫn mở được trong trình duyệt và
`tools/export_poster.py` vẫn xuất lại được PDF (sửa đường dẫn trong script). Phần "Rebuild the poster" trong README
chuyển thành một dòng trỏ tới `archive/poster_AT2A/`.

Quy tắc:

- **Chỉ `data/` chứa dữ liệu.** `app/`, `src/`, `data-eda/src/`, `notebooks/` chỉ chứa code.
  Ngoại lệ duy nhất: `app/mock/sample_ad.txt` và `sample_resume.txt`, vì đó là tính năng "dùng mẫu" của app.
- **Mỗi thứ một file.** Không giữ bản sao; bản cũ vào `archive/` kèm một dòng giải thích.
- **Mỗi thư mục một README ngắn:** file nào, dùng làm gì, ai tạo, lệnh tạo lại.
- **Mọi đường dẫn khai báo ở `src/skillabus/paths.py`.** Code, script, test, notebook đều import từ đó.
- Hình ảnh không phải dữ liệu: `data-eda/outputs/figures/` chuyển sang `docs/figures/`.

### Bảng chuyển chỗ

`archive/...` trong bảng là thư mục `archive/` ở **gốc repo**, không nằm trong `data/`.

| Hiện tại | Sau khi dọn |
|---|---|
| `data/processed/skills_seed_v2.csv` + `skill_to_esco.csv` | gộp thành `1_knowledge/skills/skills_vocabulary.csv` |
| `data-eda/config/skills_seed.csv`, `data-eda/config/skill_to_esco.csv` | `archive/dictionary_v1/` |
| `data-eda/data/clean/esco_skills_clean.csv`, `esco_label_lookup.csv` | `1_knowledge/taxonomies/` |
| `data/processed/subject_profiles.*`, `prerequisites.csv`, `offerings.csv`, `assessments_scraped.csv` | `1_knowledge/uts/` |
| `data-eda/config/subjects_template.csv`, `data/labels/subject_content_TEMPLATE.csv` | `1_knowledge/uts/` (giữ một bản) |
| `data/processed/external_courses.*` | `1_knowledge/learning_resources/` (mở rộng ở D9, D11) |
| `data/processed/skill_counts_v2.csv`, `skill_counts_2026.csv`, `top_skills.csv`, `role_profiles.*` | gộp vào `2_demand/role_skill_demand.csv`; bản gốc vào `archive/` |
| `data-eda/data/clean/jobs_au_*_clean.csv` | `2_demand/ads/` |
| `data-eda/data/clean/README.txt` | `2_demand/ads/CLEANING_NOTES.txt` |
| `data-eda/config/ats_companies.csv`, `ats_candidates.csv`, `data-eda/data/clean/ats_probe_2026-10-13.csv` | `2_demand/collection/` |
| `data/processed/emerging_candidates*.csv` | `2_demand/emerging/` |
| `data/processed/uncovered_skills_2026-10-13.csv` | `2_demand/skills_not_taught_by_uts.csv`, tính lại sau khi mở rộng |
| `data/labels/*` | `4_evaluation/labels/` |
| `data-eda/data/clean/seek_label_sample_200.csv`, `resumes_us_2021_clean.csv` | `4_evaluation/inputs/` |
| `data-eda/outputs/skill_counts_PRIMARY.csv` (mốc Seek để so), `skill_counts_linkedin_us.csv`, `skill_counts_glassdoor_au_2022.csv`, `au_vs_us_comparison.csv`, `extractor_agreement*.csv`, `source_counts.csv` | `5_crosscheck/` |
| `data-eda/outputs/esco_absent.csv`, `esco_verbphrase.csv` | `5_crosscheck/esco_coverage/` |
| `data/processed/gap.csv`, `data-eda/outputs/skill_counts.csv`, `skill_counts_wide.csv`, `ad_skill_long.csv`, `BLOCKS_B.md`, `FOR_A_blocks_3_and_5.md`, hai hình block | `archive/poster_AT2A/` (chi tiết ở mục "File nhiễu") |
| `app/mock/subject_layers.csv`, `gap_*.json` | `archive/mock_2026-10-03/`; bỏ đường dự phòng trỏ tới chúng trong `baseline.py` và `recommend.py` |
| `data-eda/outputs/figures/*.png` | `docs/figures/` |
| `data/raw/data-eda/...`, `data-eda/data/raw/` | gộp vào `data/raw/` |
| `data/cache/`, `models/esco`, `models/rag` | `runtime/cache/` |
| `data/processed/feedback.csv` | `runtime/feedback.csv` |

Kết quả: **10 chỗ còn 1**, và mở `data/` ra là thấy năm việc dữ liệu làm.

### File nhiễu (kiểm 15/10): làm cùng PR dọn thư mục

Cách kiểm: với mỗi file trên git, tìm xem code, test hay tài liệu nào nhắc tới nó.

| Loại | File | Xử lý |
|---|---|---|
| **Trông như thừa nhưng phải giữ** (công cụ đọc tự động, không cần ai nhắc tên) | `.github/*` (GitHub dùng), `.streamlit/config.toml` (Streamlit dùng), `docs/deploy.md` (hướng dẫn deploy), `data-eda/src/merge_subjects.py` (một bước scrape Handbook) | Giữ; thêm link `deploy.md` vào README |
| **Poster AT2A**, đã nộp | `poster/` (HTML, PDF A0, ảnh xem trước, logo) | `archive/poster_AT2A/poster/` |
| **Xong nhiệm vụ ở poster AT2A**, nhưng là bằng chứng cho số trên poster | `data-eda/outputs/BLOCKS_B.md`, `FOR_A_blocks_3_and_5.md`, `skill_counts.csv`, `skill_counts_wide.csv`, `ad_skill_long.csv`, `block3_sources.png`, `block5_top_skills.png`; `data/processed/gap.csv`; `docs/handoffs/` (8 file); script thời poster `extract_skills.py`, `chart_sources.py`, `chart_top15.py`, `source_counts.py` | `archive/poster_AT2A/` chia `data/`, `scripts/`, `handoffs/`. Test đọc `gap.csv` trỏ sang chỗ mới |
| **Mock cũ 70 môn**, đã có file thật thay | `app/mock/subject_layers.csv`, `gap_job_seeker.json`, `gap_role_data_scientist.json`, `build_mock.py` | `archive/mock_2026-10-03/`; bỏ đường dự phòng trong `baseline.py`, `recommend.py` |
| **Ghi chú làm việc nội bộ**, không phải tài liệu nộp | `docs/plan/data_2026-10-13.md`, `gantt.html`, `tasks_by_person.html`, `docs/superpowers/plans/`, file kế hoạch này | `docs/notes/` |
| **Công cụ poster nằm lẫn trong `src/`** | `src/export_poster.py`, `src/make_qr.py` | `archive/poster_AT2A/tools/` |
| **Hai bản của cùng một notebook** | `notebooks/vt_eda.ipynb` và `vt_eda.py` (bản text để xem diff) | Hỏi Văn Thông giữ một hay cả hai |
| **Lỗi phát hiện khi kiểm** | `data-eda/src/external/build_external.py` ghi cứng đường dẫn máy Quan `C:\MDSI\...` | Sửa bằng `paths.py` |

Rác chỉ nằm trên máy (không lên git, không ảnh hưởng người khác): `.playwright-mcp/` 109 file log trình duyệt;
`data-eda/data/raw/` 38 script và log dùng một lần; hai bản thư mục tải về (`data/raw/data-eda/`, `data-eda/data/raw/`);
`__pycache__/`; `.ua/.trash-*`. Chỉ xoá khi Quan đồng ý.

Mọi file chuyển vào `archive/` vẫn còn nguyên trong lịch sử git, nên không mất gì.

---

## 3. Một bộ từ vựng kỹ năng: ESCO làm nền, nhóm thêm phần thiếu

Thay hai file (từ điển, liên kết ESCO) bằng `1_knowledge/skills/skills_vocabulary.csv`, mỗi dòng một kỹ năng:

| Cột | Ý nghĩa |
|---|---|
| `skill_id` | Mã ESCO **chỉ khi** `esco_match = exact`; còn lại là mã riêng `skillabus:<tên>` |
| `label`, `category` | Tên hiển thị, nhóm |
| `source` | `esco` hoặc `added` (nhóm thêm vì ESCO thiếu hoặc ESCO quá rộng) |
| `esco_uri`, `esco_label` | Khái niệm ESCO liên quan, kể cả khi nó rộng hơn |
| `esco_match` | `exact`, `close`, `broad` (ESCO rộng hơn), hoặc `none`. Theo chuẩn ánh xạ SKOS mà chính ESCO dùng (exactMatch, closeMatch, broadMatch) |
| `reviewed_by` | Người kiểm liên kết ESCO của dòng này |
| `aliases_ads` | Cách tin tuyển dụng viết. **Chỉ dòng có cột này mới được dùng để dò trong tin** |
| `strict` | 1 thì phân biệt hoa thường (R, SAS, SAP, React) |
| `used_for` | `extract`, `core_skill`, hoặc cả hai |
| `why_added` | Với dòng `added`: lý do, ví dụ "ESCO không có; xuất hiện trong 12 tin" |

Ba phần trong file:

1. **148 kỹ năng hiện tại**, dùng để dò. 40 khái niệm ESCO đã liên kết mang mã ESCO; phần còn lại là `added`.
2. **Kỹ năng bắt buộc của các nghề IT đã chọn trong ESCO** (`core_skill`). Cả 75 nghề ICT có 631 kỹ năng bắt buộc;
   chỉ lấy của các nghề ứng với 11 vai trò.
3. **Kỹ năng nhóm thêm cho IT**: công cụ (từ cột O*NET "In Demand" của từng nghề, danh sách công cụ data_jobs, tin ATS),
   kỹ năng generative AI. Mỗi dòng phải có alias viết theo kiểu tin tuyển dụng và xuất hiện trong ≥ 3 tin.

**ESCO quá rộng thì giữ mã riêng.** Kiểm 47 liên kết hiện có (14/10): 20 trùng đúng; 11 dùng chung một khái niệm
rộng (Tableau và Power BI cùng là "data visualisation software"; NumPy, scikit-learn, PyTorch, matplotlib cùng là
"software components libraries"); 16 khác tên. Trong 16 dòng đó có **liên kết sai**: Transformers → "electrical
machines" (máy điện), TensorFlow và Keras → "computer vision"; cùng loại lỗi với SPARK đã chặn. Khi dựng bộ từ vựng,
mọi liên kết được gán `esco_match` và có người kiểm; liên kết sai bỏ hẳn. Nhờ mỗi kỹ năng chi tiết có mã riêng,
`match.py` so bằng `skill_id` được mà không nhầm Tableau với Power BI.

**Không dò bằng tên ESCO.** 74% tên kỹ năng nghề ICT dài từ 3 chữ ("apply information security policies"),
tin tuyển dụng không viết như vậy; nhiều tên quá chung ("manage contracts"). Bản ESCO đầy đủ 13.960 dòng giữ
trong `taxonomies/` làm bảng tra cho bước chuẩn hoá.

Câu cho báo cáo: "Skillabus mở rộng ESCO thêm N kỹ năng mà thị trường IT Úc cần nhưng ESCO chưa có."

---

## 4. Dữ liệu cho toàn ngành IT

### 4.1 Vai trò

| Nhóm | Vai trò | % Úc (data_jobs 2023) | Toàn văn Úc hiện có, xấp xỉ theo chức danh | Nguồn app dùng |
|---|---|---|---|---|
| Data & AI | Data Scientist | 1.047 tin | Seek 3.271, LinkedIn 2024 17, ATS 2026 11 | Seek toàn văn |
| Data & AI | Data Analyst | 1.362 | Seek 131, LinkedIn 2024 44, Seek 2020 22 | data_jobs |
| Data & AI | Data Engineer | 4.438 | Seek 84, LinkedIn 2024 37 | data_jobs |
| Data & AI | ML Engineer | 263 | Seek 22, ATS 2026 14, LinkedIn 2024 7 | data_jobs |
| Software | Software Engineer | 1.198 | Seek 2020 59, ATS 2026 43, Seek 66 | data_jobs |
| Software | QA/Test Engineer | — | chưa đếm | Kỹ năng cốt lõi ESCO (software tester) + O*NET 15-1253.00 |
| Cloud & hạ tầng | Cloud Engineer | 350 | Seek 2020 12, ATS 2026 11, Seek 8 | data_jobs |
| Cloud & hạ tầng | DevOps/SRE | — | chưa đếm | Kỹ năng cốt lõi ESCO + O*NET (mã cần tra) |
| Cloud & hạ tầng | Network/Systems Administrator | — | chưa đếm | ESCO (ICT network engineer) + O*NET 15-1244.00 |
| Bảo mật | Cybersecurity Analyst | — | chưa đếm | ESCO (ICT security administrator) + O*NET 15-1212.00 |
| Phân tích nghiệp vụ | Business Analyst | 576 | Seek 2020 49, Seek 10 | data_jobs |

### 4.2 Việc thu và xử lý

| # | Việc | Ra file | Ai |
|---|---|---|---|
| D1 | Viết `roles.csv`: 11 vai trò, mẫu chức danh, mã ESCO/O*NET, nguồn ưu tiên | `2_demand/roles.csv` | Văn Thông, Quan duyệt |
| D2 | Phân loại 601 tin ATS theo vai trò; fetch tiếp mỗi ngày tới 16/10 | `2_demand/ads/ats_2026_clean.csv` | Văn Thông |
| D3 | Kiểm giấy phép Seek PromptCloud 2020; dùng được thì tách phần IT | `2_demand/ads/` | Văn Thông |
| D4 | Lấy kỹ năng bắt buộc của các nghề IT từ ESCO; công cụ "In Demand" theo từng nghề từ O*NET (không dùng cờ "Hot": cờ đó tính trên toàn thị trường, nên nghề nào cũng ra Adobe, AJAX) | `1_knowledge/taxonomies/occupation_skills.csv` | Claude |
| D5 | Dựng `skills_vocabulary.csv` (mục 3) | `1_knowledge/skills/` | Claude soạn, Văn Thông duyệt |
| D6 | Đếm lại **mọi** nguồn bằng bộ từ vựng mới, ghi vào bảng nhu cầu | `2_demand/role_skill_demand.csv` | Văn Thông |
| D7 | Kiểm chéo thứ hạng toàn văn Úc với data_jobs cho vai trò có ≥ 30 tin | `5_crosscheck/role_rank_agreement.csv` | Văn Thông |
| D8 | Kiểm 44 khoá UTS đã đủ khoá IT chưa; thiếu thì scrape thêm (một luồng, ≥ 1,2 s) | `1_knowledge/uts/` | Văn Thông |
| D9 | **Kho tự học sâu và rộng**, không chỉ vá chỗ UTS thiếu (IT là ngành phải tự học suốt). Rộng: mọi kỹ năng dò được trong bộ từ vựng, ưu tiên 15 kỹ năng đầu của mỗi vai trò, mỗi kỹ năng 2–3 lựa chọn. Sâu: mỗi tài nguyên ghi `level` (cơ bản / trung cấp / nâng cao), `format` (khoá học, tài liệu chính thức, lab thực hành), `hours`, `cost` (free / free-to-audit / trả phí, AUD), `provider_type` (hãng công nghệ, đại học, cộng đồng), `date_checked`, `collected_by`; giữ các dòng text từng bài để so khớp như hiện nay. Ưu tiên nguồn chính thức của hãng | `1_knowledge/learning_resources/resources.csv`, `resource_modules.csv` | Claude thu, Akash và Văn Thông kiểm mẫu |
| D12 | **Lớp nhu cầu hiện tại cỡ mẫu lớn.** Số liệu 2019-22 giữ thứ hạng lõi (Python, SQL đứng đầu mọi giai đoạn; tương quan hạng với LinkedIn Úc 2024 = 0,69) nhưng cũ: AI 22,6% → 19/22 tin 2026, LLM 0% → 8/22, dbt 0,3% → 7,4% (2024), Hadoop 17,7% → 0/22. Mẫu 2024, 2026 trộn vai trò nên không so thẳng với Seek Data Scientist. Đếm **số tin đang đăng ở Úc** cho từng kỹ năng × vai trò qua Adzuna API (chỉ lấy `count`). Kiểm trước: Adzuna tìm trên toàn văn hay chỉ đoạn đầu; lọc ngành IT được không. Nếu được: Quan chốt lại quyết định 13/10, có thể dùng 2026 làm trọng số chính, 2019-22 làm mũi tên xu hướng | `2_demand/role_skill_demand.csv` (`source = adzuna_2026`) | Văn Thông |
| D13 | **Nhu cầu cấp vai trò từ số liệu chính phủ Úc** (Jobs and Skills Australia): (a) Occupation Shortage List 2025, nghề nào đang thiếu người (theo ACS 20/10/2025: software engineer, developer programmer, ICT QA engineer, penetration tester đã ra khỏi danh sách; cybersecurity engineer, cybersecurity operations coordinator, software tester vẫn thiếu toàn quốc); (b) Internet Vacancy Index, số tin theo nghề hằng tháng. Kiểm danh sách gốc trên trang JSA; giấy phép IVI các nguồn ghi khác nhau, kiểm trang bản quyền JSA trước khi dùng. App: nhãn "đang thiếu người ở Úc" cho vai trò | `2_demand/role_outlook.csv`: `role, anzsco_code, shortage_2025, vacancies_latest, vacancies_12m_ago, source, date` | Văn Thông |
| D14 | **Bắt buộc hay chỉ là lợi thế.** Gắn mỗi lần nhắc kỹ năng với ngữ cảnh: tiêu đề mục ("Essential", "Desirable", "Nice to have") và từ báo hiệu ("must", "required", "preferred", "bonus"). Bảng nhu cầu thêm `pct_required` cạnh `pct` | cột mới trong `role_skill_demand.csv` | Phương Nhi (trong extract) |
| D15 | **So xu hướng cùng vai trò.** Mẫu 2024, 2026 hiện trộn Data Engineer, Data Analyst với Data Scientist, nên "machine learning giảm" một phần do trộn. Đếm lại theo từng vai trò; chỉ báo xu hướng khi mỗi giai đoạn có ≥ 30 tin của vai trò đó | làm trong D6 | Văn Thông |
| D11 | **Chứng chỉ ngành, có cờ "hot" đo được.** Mỗi chứng chỉ: tên, hãng, vai trò, kỹ năng phủ, chi phí thi, `date_checked` (tên và mã thi đổi thường xuyên). Kiểm 14/10: tin trên máy hầu như không nêu tên chứng chỉ (ATS 2026: CCNA 4/601, Scrum 5/601, AWS 0; Seek IT 2020: ITIL 82/815, CCNA 13/815), dù 15–16% tin IT có chữ "certif…". Nên "hot" đo bằng: (a) **số tin đang đăng ở Úc** theo từ khoá chứng chỉ qua Adzuna API (chỉ lấy con số `count`, không cần text); (b) có trong báo cáo ngành 12 tháng gần nhất (ghi tên báo cáo, năm); (c) xu hướng nếu có hai lần đếm. Thêm chứng chỉ vào bộ từ vựng (`category = Certification`) | `1_knowledge/learning_resources/certifications.csv`: `cert, vendor, roles, skills, cost_aud, au_ads_count, count_date, report_signal, hot` | Claude soạn danh sách và kiểm trang chính thức; Văn Thông chạy Adzuna (đã có khoá API) |
| D10 | **Kỹ năng môn thật sự dạy, theo sinh viên đã học.** Handbook nông: 54/126 kỹ năng kỹ thuật không môn nào nêu tên, gồm cả TensorFlow, scikit-learn, RAG dù có dạy. Mỗi thành viên tự đăng nhập Canvas; Claude đọc trang do người đó chọn (file PDF hỏi trước từng file), chỉ ghi **tên kỹ năng** bằng lời của mình, không trích, không lưu tài liệu. Khoảng 9 môn của Quan, cộng môn của các bạn khác | `1_knowledge/uts/taught_skills_student_reported.csv`: `subject_code, skill_id, skill, collected_by, period` | Quan trước, rồi cả nhóm |

### 4.3 Bảng nhu cầu `role_skill_demand.csv`

| Cột | Ý nghĩa |
|---|---|
| `role`, `role_family` | Vai trò, nhóm ngành |
| `skill_id`, `skill` | Theo `skills_vocabulary.csv` |
| `source`, `period` | `seek_2019_22`, `data_jobs_2023`, `ats_2026`, `esco_occupation`, `onet` |
| `text_type` | `full_text`, `tool_list`, `taxonomy` (không có phần trăm) |
| `n_ads`, `total_ads`, `pct`, `pct_low`, `pct_high` | Số tin, tỷ lệ, khoảng Wilson 95%; trống với `taxonomy` |
| `importance` | `essential` / `optional` (ESCO), `in_demand` (O*NET) |

Dòng O*NET và ESCO nằm chung bảng với dòng tin tuyển dụng, phân biệt bằng `source` và `text_type`. Tên công cụ O*NET
phải đổi về `skill_id` của bộ từ vựng trước ("Amazon Web Services AWS software" → AWS); tên không đổi được thì thêm
vào bộ từ vựng (`source = added`, `why_added = O*NET in-demand cho <nghề>`) hoặc bỏ. App: thanh phần trăm lấy từ
nguồn ưu tiên trong `roles.csv`; danh sách "kỹ năng cốt lõi" lấy từ các dòng `taxonomy`.

---

## 5. Code, đánh giá, báo cáo

| # | Việc | Ai |
|---|---|---|
| C1 | `src/skillabus/paths.py`; thay khoảng 70 dòng đường dẫn trong khoảng 30 file | Claude, PR `qp/data-layout` |
| C2 | `extract`, `normalise` đọc `skills_vocabulary.csv`; `match`, `recommend` đọc `role_skill_demand.csv` theo nguồn ưu tiên | Phương Nhi, nối tiếp PR #83 |
| C3 | Ô chọn vai trò nhóm theo ngành; bỏ chữ "Data Scientist" cố định; caption ghi nguồn, năm, n, loại dữ liệu | Quan |
| C4 | `backend.py` chế độ vai trò gọi `match_role()` | Quan |
| C5 | Vai trò không có số liệu Úc: hiện "kỹ năng cốt lõi", không phần trăm | Quan |
| C6 | Mỗi kỹ năng còn thiếu hiện hai cột cạnh nhau: "Học ở UTS" và "Tự học", lọc theo trình độ và chi phí; mỗi vai trò có mục "Chứng chỉ nên có" | Quan |
| T1 | Chỉnh lại ngưỡng embedding của recommend (0,55) với khoảng 10 kỹ năng IT: notebook hiện chỉ thử 22 kỹ năng data (có Docker, AWS), trên 429 dòng môn data | Phương Nhi |
| T2 | `3_tuning/README.md`: bảng mọi tham số (giá trị, chỉnh trên dữ liệu nào, ngày, ai; hay đặt theo phán đoán) | Claude |
| T3 | Ngưỡng ESCO 0,82 ghi "tune on the labelled ads": nếu chỉnh thì dùng tin **ngoài** bộ test, nếu không thì ghi là đặt theo phán đoán | Quan |
| E1 | Gắn nhãn 20–30 tin IT: Software, Cloud, Business Analyst, Security | Akash |
| E2 | Thêm khoảng 10 cặp kỹ năng IT với môn UTS, có nhãn "n" | Hoài Thương |
| E3 | Thêm khoảng 5 câu chat về môn IT | Hoài Thương |
| E4 | Chạy lại đánh giá, tách điểm theo nhóm ngành; đo "từ điển + GPT" | Hoài Thương |
| E5 | Chạy nốt các ô **[TODO]** của chương 6 (PR #56, nhánh `ht/eval-subjects-chat`): GPT trên 20 tin (cache có sẵn ở PR #94), embeddings cho P@3 môn và chat, LLM chấm câu trả lời chat, baseline TF-IDF/embedding cho xếp câu CV | Hoài Thương |
| E6 | **Chấm GPT công bằng:** nhãn của Hoài Thương chỉ có kỹ năng trong từ điển, nên kỹ năng mới GPT tìm đúng vẫn bị tính sai. Nhãn của Văn Thông trên cùng 20 tin có 32% kỹ năng ngoài từ điển: dùng làm bộ chấm thứ hai cho GPT và kỹ năng mới nổi | Hoài Thương |
| R1 | Báo cáo: phạm vi "data và IT roles"; bảng nguồn theo vai trò có cột giấy phép; câu mở rộng ESCO; sửa câu O*NET | Văn Thông (03), Akash (07), Quan (01) |

Giữ luật: không chỉnh ngưỡng hay prompt trên tin trong bộ test.

---

## 6. Phân công 3 ngày (năm người + Claude chạy song song)

### Bước 0: dọn nhánh trước, rồi mới dời thư mục (kiểm 15/10)

Ý của Quan: merge xong việc dở trước, xoá nhánh cũ, rồi mọi người tạo nhánh mới từ layout mới để không ai bị ảnh hưởng.

Tình trạng 26 nhánh trên GitHub:

| Nhóm | Nhánh | Ảnh hưởng khi dời thư mục | Xử lý |
|---|---|---|---|
| **Đã merge** (11) | `vt/ats-2026`, `vt/resume-deid`, `vt/role-profiles`, `vt/ad-skills-second`, `ht/cv-jd-pairs`, `ht/ad-skills-overlap`, `ht/subject-pairs-chat-questions`, `ak/related-work`, `pn/methods-update`, `pn/emerging-skills`, `qp/handbook-scrape` | Không: việc đã nằm trong `main` | Xoá nhánh. An toàn: GitHub có nút khôi phục nhánh trên trang PR |
| **Nặng**: sửa file nằm trong thư mục sẽ dời | #94 `qp/review-followups` (31), #97 `vt/report-03` (9), #98 `qp/antirequisite-fix` (3), #99 `vt/ats-rerun` (2), `vt/external-check` (2, **chưa có PR**), #56 `ht/eval-run` và `ht/eval-subjects-chat` (**chưa có PR**, 11 commit), #80 `qp/ideas` | Xung đột nếu dời trước | **Merge trước khi dời** |
| **Nhẹ**: chỉ sửa code đọc đường dẫn | #82 `pn/prerequisites`, #83 `pn/two-tier`, #54 `ht/eval-fixes` (đang xung đột sẵn) | Vài dòng đường dẫn | Merge trước nếu kịp; nếu không, rebase sau, Claude giúp |
| **Không ảnh hưởng**: chỉ sửa báo cáo | #88 `ak/phases-challenges`, #89 `ak/ethics-review`, #91 `ak/appendix` | Không | Merge lúc nào cũng được |

Thứ tự ngày 15/10:

| Giờ | Việc | Ai |
|---|---|---|
| Sáng tới 12:00 | Claude review cả 14 nhánh; chủ nhánh sửa theo review; merge theo thứ tự phụ thuộc: #98 → #82 → #83; #94; #97; #99; #56 gộp với `ht/eval-subjects-chat`; `vt/external-check` mở PR rồi merge; #54 rebase; #80 | Claude review thay Quan; PR của Quan (#80, #94, #98) cần Văn Thông duyệt |
| 12:00 | **Đóng băng:** không ai đẩy thay đổi vào `data/`, `data-eda/`, `src/`, `app/` | Cả nhóm |
| 12:00–14:00 | PR dọn thư mục (C1 + file nhiễu + archive); test và app chạy được; Văn Thông duyệt; merge | Claude, Văn Thông |
| 14:00 | Xoá nhánh đã merge. Mọi người: `git fetch --prune`, `git switch main`, `git pull`, tạo nhánh mới cho việc tiếp theo | Quan bấm xoá; cả nhóm |
| Sau 14:00 | PR nào chưa kịp merge: chủ nhánh rebase lên `main` mới. Nhờ `git mv`, sửa đổi trong file dữ liệu tự đi theo chỗ mới; dòng đường dẫn trong code đổi sang `paths.py`. Claude giúp từng người | Chủ nhánh, Claude |

Luật: **không xoá nhánh chưa merge** khi chủ nhánh chưa đồng ý. Hai nhánh chưa có PR (`vt/external-check`,
`ht/eval-subjects-chat`) phải mở PR trước để không mất việc.

### Phân công

Điều kiện tiên quyết: **Bước 0 và PR dọn thư mục (C1) xong trước**, mốc 14:00 ngày 15/10. Sau đó cả nhóm làm trên
cấu trúc mới; nhờ `paths.py`, PR nào rebase cũng chỉ phải đổi vài dòng đường dẫn.

| Người | 15/10 | 16/10 | 17/10 |
|---|---|---|---|
| **Quan** (Claude làm theo lệnh) | Review và merge PR theo thứ tự; D10 các môn của Quan qua Canvas | C3–C6 app: chọn vai trò, kỹ năng cốt lõi, hai cột UTS / tự học, chứng chỉ | Đóng băng, chạy lại, nộp; chương 1 |
| **Claude** (song song, có thể chia agent) | D4 + D5 bộ từ vựng; danh sách chứng chỉ D11 | D9 kho tự học, chia theo nhóm vai trò | Sửa lỗi theo kết quả kiểm |
| **Văn Thông** | D1 `roles.csv`; D2 phân loại tin ATS; D3 giấy phép Seek 2020; duyệt D5; D12 kiểm và chạy đếm Adzuna (kỹ năng, chứng chỉ); D13 số liệu chính phủ | D6 đếm lại, bảng nhu cầu, gồm D15 so cùng vai trò; D7 kiểm chéo; D8 khoá UTS | Chương 3 |
| **Phương Nhi** | Sửa #82, #83 theo review rồi merge; D10 môn của mình | C2 pipeline đọc bộ từ vựng, bảng nhu cầu, kho tự học; D14 gắn cờ bắt buộc / lợi thế | Kiểm số trên app |
| **Hoài Thương** | D10 môn của mình; E2 10 cặp kỹ năng IT với môn; E3 5 câu chat | E4 chạy lại đánh giá, tách theo nhóm ngành | Chương 6 |
| **Akash** | E1 gắn nhãn 20–30 tin IT, lấy ngay từ file ATS 601 tin | Kiểm mẫu link và giá của D9, D11; chương 7 | Chương 9, phụ lục |

Phụ thuộc cần canh:

- D5 (bộ từ vựng) phải xong trước D6 (đếm lại) và C2 (pipeline). Mốc: tối 15/10.
- E1 không phải chờ: tin ATS đã có sẵn trên máy Văn Thông và Quan.
- D10 mỗi người làm độc lập, khoảng 1–2 giờ.

Luật làm chung: mỗi file dữ liệu một người chủ; sửa file của người khác thì qua PR và báo người chủ; mọi PR vào
`main` qua review của Quan (Claude review thay).

Các PR đang chạm dữ liệu cần rebase sau bước 1: #94 (31 file dữ liệu), #97 (6), #98 (2), #56 (1); #82 và #83 sửa
`match.py`, `recommend.py`. Dời bằng `git mv` để Git nhận ra file đổi chỗ.

## 7. Rủi ro

| Rủi ro | Cách giảm |
|---|---|
| Dời thư mục sát hạn làm vỡ code, xung đột PR | Một PR; `paths.py`; chạy test và app trước khi merge; ghi rõ PR nào cần rebase |
| Không kịp hết các việc D, C, E | PR dọn thư mục tự nó đã đáng giá; bảng nhu cầu có thể bắt đầu chỉ với 7 vai trò data_jobs + 4 vai trò kỹ năng cốt lõi; kho tự học ưu tiên 15 kỹ năng đầu mỗi vai trò, phần còn lại ghi "bước tiếp theo" |
| Năm người sửa dữ liệu cùng lúc | Mỗi file một người chủ; mọi thay đổi qua PR; Claude review |
| Phần trăm từ nguồn khác nhau bị so như cùng thước đo | Cột `text_type`, caption ghi nguồn và năm |
| Bộ từ vựng mới làm đổi số poster | Số poster đóng băng trong `archive/poster_AT2A/` |
| Seek 2020 không rõ giấy phép | Kiểm trước (D3); không rõ thì bỏ |
| Scrape UTS bị chặn | Một luồng, ≥ 1,2 s, báo trong PR trước khi chạy |

---

## Phụ lục A: tin nhắn cho nhóm (tiếng Anh, vì có Akash)

> **Skillabus: branch clean-up and new data layout, Wed 15 Oct**
>
> We are moving to a cleaner repo before the final push: all data goes into one `data/` folder sorted by use
> (knowledge, demand, tuning, evaluation, cross-check), old poster files go into one `archive/` folder, and the app
> covers all IT roles, not only Data Scientist. Full plan: `docs/notes/data_it_scope_2026-10-14.md`.
>
> To make sure nobody loses work:
>
> 1. **By 12:00 today**, get your open PR ready to merge. I'll review all of them this morning; please answer the
>    comments quickly.
>    - Van Thong: #97, #99, and please open a PR for `vt/external-check`. Please also review my #80, #94, #98.
>    - Phuong Nhi: #82, then #83.
>    - Hoai Thuong: #56 together with `ht/eval-subjects-chat` (it has no PR yet), and rebase #54.
>    - Akash: #88, #89, #91.
> 2. **12:00 to 14:00: freeze.** Please don't push changes to `data/`, `data-eda/`, `src/` or `app/` while the
>    layout PR goes in.
> 3. **From 14:00:** `git fetch --prune`, `git switch main`, `git pull`, then start a new branch for your next task.
>    Merged branches will be deleted. If your PR didn't make it in time, rebase it on the new `main`; file moves are
>    done with `git mv`, so your edits follow the files. Ask me if anything conflicts.
>
> Unmerged branches are never deleted without their owner's OK.
>
> Quan
