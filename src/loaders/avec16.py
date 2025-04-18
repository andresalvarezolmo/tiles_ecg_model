import os, numpy as np
import pandas as pd, neurokit2 as nk
from tqdm import tqdm
from pathlib import Path
from torch.utils import data
from scipy.signal import resample_poly


class AVEC16(data.Dataset):
    def __init__(self, root, sr, split="train", category="arousal"):
        super().__init__()
        self.root = root
        self.sr = sr
        self.win = sr * 10
        split = "dev" if split == "test" else split
        print(os.path.exists(f"data/avec16/{split}_lab_{category}.npy"))

        if os.path.exists(f"data/avec16/{split}_lab_{category}.npy"):
            print("Loading from cache...")
            self.samples = np.load(f"data/avec16/{split}_ecg.npy")
            self.labels = np.load(f"data/avec16/{split}_lab_{category}.npy")
        else:
            print("Loading ECG data...")
            data_path = Path(self.root)

            ecg_data, ecg_labels = list(), list()
            for participant_id in tqdm(range(1, 10)):
                annotation_path = data_path.joinpath(
                    "ratings_gold_standard", category, f"{split}_{participant_id}.arff"
                )
                ecg_data_path = data_path.joinpath(
                    "recordings_physio", "filtered", f"{split}_{participant_id}.csv"
                )
                # Read ECG data
                ecg = pd.read_csv(ecg_data_path, delimiter=";")["ECG"].values
                new_len = int((len(ecg) / 250) * self.sr)
                ecg = resample_poly(ecg, self.sr, 250)[:new_len]

                with open(annotation_path) as f:
                    lines = f.readlines()
                    for line in lines:
                        if f"{split}_{participant_id}" not in line:
                            continue
                        time = float(line.split(",")[-2].split("\n")[0])
                        # We skip the first 10s of ECG data
                        # We select data frames every 20ms
                        if time <= 10:
                            continue
                        if (time * 100) % 20:
                            continue

                        # Read data and labels
                        label = float(line.split(",")[-1].split("\n")[0])
                        start_idx = int(time * 100 - self.win)
                        end_idx = int(time * 100)
                        data = ecg[start_idx:end_idx]

                        # ECG Data cleaning
                        data = nk.ecg_clean(data, sampling_rate=self.sr)
                        mean, std = np.mean(data, axis=0), np.std(data, axis=0)
                        data = (data - mean) / (std + 1e-5)

                        ecg_data.append(data)
                        ecg_labels.append(label)

            self.samples = np.array(ecg_data)
            self.labels = np.array(ecg_labels)

            os.makedirs("data/avec16", exist_ok=True)
            np.save(f"data/avec16/{split}_ecg.npy", self.samples)
            np.save(f"data/avec16/{split}_lab_{category}.npy", self.labels)

        print(f"Loaded {len(self.labels)} ECG samples in total.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        ecg = self.samples[idx]
        lab = self.labels[idx]
        return ecg, lab, 0


if __name__ == "__main__":
    root = "/media/data/sail-data/Recola/AVEC16"
    train_dataset = AVEC16(root, sr=100, split="train", category="valence")
    dev_dataset = AVEC16(root, sr=100, split="dev", category="valence")
    print(train_dataset[0][0].shape, train_dataset[0][1])
