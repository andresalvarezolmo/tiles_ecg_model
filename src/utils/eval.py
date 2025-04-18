import torch, numpy as np
from tqdm import tqdm
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, precision_score, recall_score

from .ccc import mean_ccc

def evaluate(model, dataset, dataset_name, aggregate="majority", modalities=["ecg", "eda"]):
    """
    Performs evaluation of trained supervised models
    Args:
        model (pytorch_lightning.LightningModule): Supervised model to evaluate.
        dataset (torch.utils.data.Dataset): Test dataset.
        dataset_name (str): Name of dataset.
        aggregate (str): Method to aggregate instance-level outputs
    Returns:
        global_metrics (dict): Dictionary containing performance metrics
    """
    model.eval()
    # print("Evaluating model...")

    y_true, y_pred, y_name = [], [], []
    for data, label, name in tqdm(dataset):
        # move inputs to device
        if isinstance(data, dict):
            data = {key: data[key].to(model.device) for key in modalities}
        else:
            data = data.to(model.device)

        label = label.to(model.device)
        with torch.no_grad():
            preds, y = model(data, label)
            if (
                "ptb" not in dataset_name
                and "AVEC" not in dataset_name
                and "EPIC" not in dataset_name
            ):
                preds = preds.argmax(dim=1).detach()
                y = y.long().detach()

            # save labels and predictions
            y_true.append(y)
            y_pred.append(preds)
            y_name.extend(name)

    # stack arrays for evaluation
    y_true = torch.cat(y_true, dim=0).squeeze().cpu().numpy()
    y_pred = torch.cat(y_pred, dim=0).squeeze().cpu().numpy()
    y_name = np.array(y_name)

    if "EPIC" in dataset_name:
        return y_pred, None

    # chunk-wise predictions
    if "ptb" in dataset_name:
        auc = roc_auc_score(y_true, y_pred)
        y_pred = 1 / (1 + np.exp(-y_pred)) > 0.5
        f1 = f1_score(y_true, y_pred * 1, average="macro", zero_division=0)
        y_pred_binary = np.zeros_like(y_pred, dtype=bool)
        y_pred_binary[np.arange(y_pred.shape[0]), np.argmax(y_pred, axis=1)] = True
        tn = np.sum((y_true == 0) & (y_pred_binary == 0))
        fp = np.sum((y_true == 0) & (y_pred_binary == 1))
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        precision = precision_score(y_true, y_pred_binary, average="macro", zero_division=0)
        recall = recall_score(y_true, y_pred_binary, average="macro", zero_division=0)
        acc = accuracy_score(y_true, y_pred_binary)
        metrics = {"Accuracy": acc, "AUROC": auc, "F1-macro": f1, "Specificity": specificity, "Precision": precision, "Recall": recall}
    elif "AVEC" in dataset_name:
        ccc = mean_ccc(y_pred, y_true)
        metrics = {"CCC": ccc}
    else:
        print("y_true", y_true.shape, y_true)
        print("y_pred", y_pred.shape, y_pred)
        acc = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
        precision = precision_score(y_true, y_pred, average="macro", zero_division=0)
        recall = recall_score(y_true, y_pred, average="macro", zero_division=0)
                # Calculate specificity (true negative rate) for binary classification
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        metrics = {"Accuracy": acc, "F1-macro": f1, "Specificity": specificity, "Precision": precision, "Recall": recall}


    print(f"Chunk-wise results for {dataset_name}:\n{metrics}")

    # aggregate predictions
    y_true_agg, y_pred_agg = [], []
    if "ptb" in dataset_name or "AVEC" in dataset_name:
        metrics_agg = None
    else:
        for name in np.unique(y_name):
            idx = np.where(y_name == name)[0]
            these_preds = y_pred[idx]
            these_labels = y_true[idx]
            for label in np.unique(these_labels):
                y_true_agg.append(label)
                fidx = np.where(these_labels == label)[0]
                if aggregate == "majority":
                    y_pred_agg.append(np.bincount(these_preds[fidx]).argmax())
                else:
                    raise NotImplementedError

        acc = accuracy_score(y_true_agg, y_pred_agg)
        f1 = f1_score(y_true_agg, y_pred_agg, average="macro", zero_division=0)
        acc = accuracy_score(y_true_agg, y_pred_agg)
        f1 = f1_score(y_true_agg, y_pred_agg, average="macro", zero_division=0)
        precision = precision_score(y_true_agg, y_pred_agg, average="macro", zero_division=0)
        recall = recall_score(y_true_agg, y_pred_agg, average="macro", zero_division=0)
        tn = np.sum((y_true_agg == 0) & (y_true_agg == 0))
        fp = np.sum((y_true_agg == 0) & (y_true_agg == 1))
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0

        metrics_agg = {"Accuracy": acc, "F1-macro": f1, "Specificity": specificity, "Precision": precision, "Recall": recall}
        print(f"Aggregated results for {dataset_name}:\n{metrics_agg}")

    return metrics, metrics_agg
