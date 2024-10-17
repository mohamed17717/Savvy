def labels_by_bert(texts):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, logging

    logging.set_verbosity_error()

    model_name = "bert-base-multilingual-cased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    labels = []
    for text in texts:
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)

        with torch.no_grad():
            logits = model(**inputs).logits

        predicted_class = torch.argmax(logits, dim=1).item()
        labels.append(predicted_class)

    return labels


def labels_by_sklearn(texts):
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)

    num_clusters = 10
    kmeans = KMeans(n_clusters=num_clusters, random_state=0, n_init=10)
    cluster_labels = kmeans.fit_predict(tfidf_matrix)

    return cluster_labels


def phrase_negativity_distilbert():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

    model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    classifier = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    res = classifier("i've waiting for a HuggingFace course my whole life")
    return res
