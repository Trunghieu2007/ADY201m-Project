import os
import sys
import re
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Đảm bảo in tiếng Việt chuẩn trên Windows terminal và matplotlib
sys.stdout.reconfigure(encoding="utf-8")
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
MODEL_PATH = os.path.join(BASE_DIR, "category_classifier_model.joblib")
VECTORIZER_PATH = os.path.join(BASE_DIR, "tfidf_vectorizer.joblib")
CONFUSION_MATRIX_PATH = os.path.join(BASE_DIR, "confusion_matrix.png")
METRICS_PATH = os.path.join(BASE_DIR, "evaluation_metrics.json")

# Danh sách ứng viên file dữ liệu đầu vào trực tiếp từ Web crawler (hoàn toàn không dùng SQL)
DATA_CANDIDATES = [
    os.path.join(PROJECT_DIR, "Web crawler", "vnexpress_data.json"),
    os.path.join(PROJECT_DIR, "Web crawler", "vnexpress_historical_data.csv"),
    os.path.join(PROJECT_DIR, "Web crawler", "vnexpress_data.csv"),
    os.path.join(BASE_DIR, "vnexpress_data.json"),
    os.path.join(BASE_DIR, "vnexpress_data.csv"),
]

def load_crawler_data():
    """Tải dữ liệu cào trực tiếp từ các file CSV/JSON của Web crawler."""
    found_path = None
    for path in DATA_CANDIDATES:
        if os.path.exists(path):
            found_path = path
            break

    if not found_path:
        raise FileNotFoundError(
            f"[!] Không tìm thấy file dữ liệu từ Web crawler trong các vị trí: {DATA_CANDIDATES}"
        )

    print(f"[*] Nạp dữ liệu cào trực tiếp từ: {os.path.relpath(found_path, PROJECT_DIR)}")
    if found_path.endswith(".json"):
        with open(found_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        df = pd.read_csv(found_path)

    # Ghép thêm dữ liệu đợt cào mới nhất nếu đang dùng tập historical
    latest_csv = os.path.join(PROJECT_DIR, "Web crawler", "vnexpress_data.csv")
    if found_path != latest_csv and os.path.exists(latest_csv):
        df_latest = pd.read_csv(latest_csv)
        df = pd.concat([df, df_latest], ignore_index=True)
        if "article_id" in df.columns:
            df = df.drop_duplicates(subset=["article_id"], keep="last")

    return df

def clean_vietnamese_text(text):
    """Làm sạch văn bản cơ bản: loại bỏ thẻ thừa, ký tự đặc biệt, chuẩn hóa khoảng trắng."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)  # bỏ url
    text = re.sub(r"[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def preprocess_dataset(df):
    """Chuẩn hóa dữ liệu theo chỉ dẫn của AI Agent Guide (Data Preparation)."""
    # Lấy tiêu đề, mô tả và nội dung ghép lại để tạo biểu diễn thông tin ngữ cảnh đầy đủ nhất
    titles = df["title"].fillna("")
    descriptions = df["description"].fillna("")
    contents = df["content"].fillna("")

    full_text = titles + " " + descriptions + " " + contents
    df["clean_text"] = full_text.apply(clean_vietnamese_text)

    # Lọc bỏ các bài không có nội dung hoặc thuộc chuyên mục 'Khác'
    df = df[df["clean_text"].str.strip().str.len() > 20].copy()
    if "category" in df.columns:
        df = df[df["category"].notna()].copy()
        df = df[df["category"].str.strip() != "Khác"].copy()

    # Lọc các chuyên mục có số mẫu tối thiểu >= 4 để đảm bảo phân chia train/test hợp lệ
    counts = df["category"].value_counts()
    valid_categories = counts[counts >= 4].index
    df = df[df["category"].isin(valid_categories)].copy()

    print(f"[*] Dữ liệu sau chuẩn hóa: {len(df)} bài báo thuộc {len(valid_categories)} chuyên mục hợp lệ.")
    return df

def plot_confusion_matrix(cm, labels, save_path):
    """Vẽ và lưu ma trận nhầm lẫn (Confusion Matrix) dưới dạng Heatmap trực quan."""
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)

    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=labels,
        yticklabels=labels,
        title="Ma trận nhầm lẫn (Confusion Matrix) - Phân loại chuyên mục",
        ylabel="Chuyên mục thực tế (True Label)",
        xlabel="Chuyên mục dự đoán (Predicted Label)",
    )

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Điền giá trị vào từng ô
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = cm[i, j]
            ax.text(
                j, i, format(val, "d") if val > 0 else "0",
                ha="center", va="center",
                color="white" if val > thresh else "black",
                fontsize=8, fontweight="bold" if val > 0 else "normal"
            )

    fig.tight_layout()
    fig.savefig(save_path, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"[+] Đã lưu biểu đồ ma trận nhầm lẫn tại: {os.path.relpath(save_path, PROJECT_DIR)}")

def train_and_evaluate():
    """Quy trình Phase 7 (Huấn luyện) & Phase 8 (Đánh giá chẩn đoán) theo chỉ dẫn John Rollins."""
    print("=" * 65)
    print(" GIAI ĐOẠN 7 & 8: HUẤN LUYỆN VÀ ĐÁNH GIÁ MÔ HÌNH AI PHÂN LOẠI ")
    print(" (Xử lý độc lập từ Web crawler, không phụ thuộc CSDL) ")
    print("=" * 65)

    # 1. Nạp và chuẩn hóa dữ liệu
    df = load_crawler_data()
    df = preprocess_dataset(df)

    X = df["clean_text"]
    y = df["category"]

    # 2. Phân chia Train/Test độc lập (Gate 1 - Toàn vẹn dữ liệu, chống rò rỉ)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"[*] Phân chia tập dữ liệu: {len(X_train)} bài train (80%) | {len(X_test)} bài test (20%)")

    # 3. Trích xuất đặc trưng văn bản bằng TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=4000,
        ngram_range=(1, 2),
        sublinear_tf=True
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    print(f"[*] Kích thước ma trận TF-IDF: {X_train_vec.shape}")

    # 4. Huấn luyện mô hình Cây quyết định (Decision Tree) theo chỉ định tài liệu
    print("\n[*] Đang huấn luyện mô hình Decision Tree Classifier...")
    dt_model = DecisionTreeClassifier(
        criterion="gini",
        max_depth=25,
        min_samples_split=4,
        random_state=42
    )
    dt_model.fit(X_train_vec, y_train)

    # Huấn luyện mô hình đối chứng Naive Bayes
    nb_model = MultinomialNB(alpha=0.1)
    nb_model.fit(X_train_vec, y_train)

    # 5. Đánh giá chẩn đoán trên tập kiểm tra độc lập (Gate 2 & Gate 3)
    dt_pred = dt_model.predict(X_test_vec)
    nb_pred = nb_model.predict(X_test_vec)

    dt_acc = accuracy_score(y_test, dt_pred)
    nb_acc = accuracy_score(y_test, nb_pred)

    print("\n" + "-" * 50)
    print("KẾT QUẢ ĐÁNH GIÁ CHẨN ĐOÁN (DIAGNOSTIC MEASURES)")
    print("-" * 50)
    print(f"Độ chính xác Decision Tree (Chủ đạo): {dt_acc * 100:.2f}%")
    print(f"Độ chính xác Naive Bayes (Đối chứng): {nb_acc * 100:.2f}%")

    # Chi tiết báo cáo phân loại cho mô hình chủ đạo Decision Tree
    labels = sorted(list(y.unique()))
    report_dict = classification_report(y_test, dt_pred, target_names=labels, output_dict=True, zero_division=0)
    report_text = classification_report(y_test, dt_pred, target_names=labels, zero_division=0)
    print("\nBáo cáo phân loại chi tiết (Decision Tree):")
    print(report_text)

    # 6. Vẽ và lưu Ma trận nhầm lẫn
    cm = confusion_matrix(y_test, dt_pred, labels=labels)
    plot_confusion_matrix(cm, labels, CONFUSION_MATRIX_PATH)

    # 7. Trích xuất Top từ khóa đặc trưng (Feature Importance - Gate 3)
    importances = dt_model.feature_importances_
    feature_names = np.array(vectorizer.get_feature_names_out())
    top_indices = np.argsort(importances)[::-1][:15]

    print("\nTop 15 đặc trưng (từ khóa) có trọng số quyết định cao nhất trong Cây quyết định:")
    top_features = []
    for rank, idx in enumerate(top_indices, 1):
        feat = feature_names[idx]
        imp = importances[idx]
        top_features.append({"rank": rank, "feature": feat, "importance": round(float(imp), 4)})
        print(f"  {rank:2d}. {feat:<20} : {imp:.4f}")

    # 8. Lưu mô hình và chỉ số đánh giá phục vụ tái lập kết quả
    joblib.dump(dt_model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    metrics_summary = {
        "accuracy_decision_tree": round(float(dt_acc), 4),
        "accuracy_naive_bayes": round(float(nb_acc), 4),
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "num_categories": int(len(labels)),
        "categories": labels,
        "top_features": top_features,
        "classification_report": report_dict
    }

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, ensure_ascii=False, indent=4)

    print(f"\n[+] Đã lưu mô hình tại: {os.path.relpath(MODEL_PATH, PROJECT_DIR)}")
    print(f"[+] Đã lưu bộ vector hóa TF-IDF tại: {os.path.relpath(VECTORIZER_PATH, PROJECT_DIR)}")
    print(f"[+] Đã lưu chỉ số đánh giá tại: {os.path.relpath(METRICS_PATH, PROJECT_DIR)}")
    print("=" * 65)
    print(" HOÀN TẤT GIAI ĐOẠN HUẤN LUYỆN VÀ ĐÁNH GIÁ MÔ HÌNH AI ")
    print("=" * 65)

    return dt_model, vectorizer

def predict_article_category(title, description, content):
    """Hàm phụ trợ: Dự đoán chuyên mục cho một bài báo mới chưa dán nhãn."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        raise FileNotFoundError("Mô hình chưa được huấn luyện. Hãy chạy train_and_evaluate() trước.")

    model = joblib.load(MODEL_PATH)
    vec = joblib.load(VECTORIZER_PATH)

    raw_text = f"{title} {description} {content}"
    clean = clean_vietnamese_text(raw_text)
    x_vec = vec.transform([clean])
    predicted_cat = model.predict(x_vec)[0]
    return predicted_cat

if __name__ == "__main__":
    train_and_evaluate()
