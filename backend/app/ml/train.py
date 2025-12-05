"""
Enhanced ML Training Script for Tajweed Classifiers
Supports multiple error types with audio feature extraction
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import librosa
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Audio processing parameters
SAMPLE_RATE = 16000
N_MFCC = 40
N_FFT = 2048
HOP_LENGTH = 512
MAX_DURATION = 5.0  # seconds


class QuranAudioDataset(Dataset):
    """Dataset for Quran audio with tajweed labels"""
    
    def __init__(self, manifest_path: str, error_type: str, data_dir: Path):
        self.data_dir = data_dir
        self.error_type = error_type
        self.samples = []
        
        # Load manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        # Filter for samples with this error type
        for item in manifest:
            audio_path = data_dir.parent / item["audio_path"]
            if not audio_path.exists():
                continue
            
            # Check if this ayah has the specific tajweed rule
            tajweed_rules = item.get("tajweed_rules", {})
            has_error = error_type in tajweed_rules
            
            self.samples.append({
                "audio_path": str(audio_path),
                "label": 1 if has_error else 0,  # Binary classification
                "metadata": item
            })
        
        logger.info(f"Loaded {len(self.samples)} samples for {error_type}")
        logger.info(f"Positive examples: {sum(s['label'] for s in self.samples)}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        # Load and process audio
        try:
            audio, sr = librosa.load(sample["audio_path"], sr=SAMPLE_RATE, duration=MAX_DURATION)
            
            # Extract MFCC features
            mfcc = librosa.feature.mfcc(
                y=audio,
                sr=sr,
                n_mfcc=N_MFCC,
                n_fft=N_FFT,
                hop_length=HOP_LENGTH
            )
            
            # Normalize and pad/trim to fixed length
            max_frames = int(MAX_DURATION * SAMPLE_RATE / HOP_LENGTH)
            if mfcc.shape[1] < max_frames:
                mfcc = np.pad(mfcc, ((0, 0), (0, max_frames - mfcc.shape[1])))
            else:
                mfcc = mfcc[:, :max_frames]
            
            features = torch.FloatTensor(mfcc)
            label = torch.LongTensor([sample["label"]])
            
            return features, label
            
        except Exception as e:
            logger.error(f"Error loading {sample['audio_path']}: {e}")
            # Return zero tensor on error
            max_frames = int(MAX_DURATION * SAMPLE_RATE / HOP_LENGTH)
            return torch.zeros(N_MFCC, max_frames), torch.LongTensor([0])


class TajweedCNN(nn.Module):
    """CNN model for tajweed classification"""
    
    def __init__(self, n_classes=2):
        super(TajweedCNN, self).__init__()
        
        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        
        # Calculate flattened size
        # Input: (40, max_frames) -> after 3 pools: (40/8, max_frames/8)
        max_frames = int(MAX_DURATION * SAMPLE_RATE / HOP_LENGTH)
        flat_size = 128 * (N_MFCC // 8) * (max_frames // 8)
        
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(flat_size, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, n_classes)
        )
    
    def forward(self, x):
        # Add channel dimension
        x = x.unsqueeze(1)
        
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.fc(x)
        
        return x


def train_model(
    manifest_path: str,
    error_type: str,
    epochs: int = 30,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
):
    """Train tajweed classifier"""
    logger.info(f"Training classifier for: {error_type}")
    logger.info(f"Device: {device}")
    
    # Load dataset
    data_dir = Path(manifest_path).parent
    dataset = QuranAudioDataset(manifest_path, error_type, data_dir)
    
    # Split train/val
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # Initialize model
    model = TajweedCNN(n_classes=2).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    best_val_acc = 0.0
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for features, labels in train_loader:
            features = features.to(device)
            labels = labels.squeeze().to(device)
            
            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for features, labels in val_loader:
                features = features.to(device)
                labels = labels.squeeze().to(device)
                
                outputs = model(features)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
        
        train_acc = 100. * train_correct / train_total
        val_acc = 100. * val_correct / val_total
        
        logger.info(f"Epoch {epoch+1}/{epochs}")
        logger.info(f"  Train Loss: {train_loss/len(train_loader):.4f}, Acc: {train_acc:.2f}%")
        logger.info(f"  Val Loss: {val_loss/len(val_loader):.4f}, Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            model_path = data_dir / f"model_{error_type}.pth"
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
            }, model_path)
            logger.info(f"  ✓ Saved best model (val_acc: {val_acc:.2f}%)")
    
    logger.info(f"\nTraining complete! Best validation accuracy: {best_val_acc:.2f}%")
    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/ml_training/training_manifest.json")
    parser.add_argument("--error_type", default="madd_2", choices=[
        "madd_2", "madd_6", "madd_246", "madd_muttasil", "madd_munfasil",
        "ghunnah", "idghaam_ghunnah", "idghaam_no_ghunnah",
        "ikhfa", "ikhfa_shafawi", "iqlab", "qalqalah"
    ])
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    
    args = parser.parse_args()
    
    train_model(
        manifest_path=args.manifest,
        error_type=args.error_type,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )
