import os
# Tắt cảnh báo Symlinks khó chịu trên Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import numpy as np
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='binary')
    acc = accuracy_score(labels, predictions)
    return {'accuracy': acc, 'f1': f1, 'precision': precision, 'recall': recall}


def train_gec_model():
    print("[INFO] Đang tải tập dữ liệu CoLA từ Hugging Face...")
    # SỬA LỖI TẠI ĐÂY: Thêm namespace nyu-mll/ vào trước glue
    dataset = load_dataset("nyu-mll/glue", "cola")

    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize_function(examples):
        return tokenizer(examples["sentence"], padding="max_length", truncation=True, max_length=128)

    print("[INFO] Đang Tokenize dữ liệu...")
    tokenized_datasets = dataset.map(tokenize_function, batched=True)

    # Label 1: Acceptable (Đúng ngữ pháp), Label 0: Unacceptable (Sai ngữ pháp)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

    # Tạo thư mục chứa model nếu chưa có
    output_dir = "./app/ml_models/saved_models/gec_transformer"
    os.makedirs(output_dir, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=output_dir,
        learning_rate=2e-5,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=32,
        num_train_epochs=3,
        weight_decay=0.01,
        eval_strategy="epoch",  # Cập nhật từ evaluation_strategy sang eval_strategy theo phiên bản mới
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )

    print("[INFO] Bắt đầu quá trình Fine-tuning...")
    trainer.train(resume_from_checkpoint=True)

    print(f"[INFO] Lưu mô hình Local GEC tại: {output_dir}")
    trainer.save_model(output_dir)


if __name__ == "__main__":
    train_gec_model()