"""
ML Training Pipeline for Tajweed Error Classification

This script trains classifiers for each tajweed error type using
labeled audio data from Label Studio.

Usage:
    python train.py --config config/training_config.yaml
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import json

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchaudio
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import wandb  # Optional: for experiment tracking

# Local imports (to be implemented)
# from models.classifier import TajweedClassifier
# from data.dataset import TajweedDataset
# from utils.augmentation import AudioAugmentation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TajweedDataset(Dataset):
    """
    Dataset for tajweed error classification
    
    Loads audio clips and their labels from Label Studio exports.
    """
    
    def __init__(
        self, 
        data_path: str, 
        error_type: str,
        transform=None,
        sample_rate: int = 16000,
        duration: float = 1.0
    ):
        """
        Args:
            data_path: Path to Label Studio JSON export
            error_type: Type of error to train for (e.g., 'madd_short')
            transform: Optional audio augmentation transforms
            sample_rate: Target sample rate
            duration: Fixed duration for audio clips (seconds)
        """
        self.data_path = Path(data_path)
        self.error_type = error_type
        self.transform = transform
        self.sample_rate = sample_rate
        self.duration = duration
        self.target_length = int(sample_rate * duration)
        
        # Load annotations
        self.samples = self._load_annotations()
        logger.info(f"Loaded {len(self.samples)} samples for {error_type}")
    
    def _load_annotations(self) -> List[Dict]:
        """Load and parse Label Studio annotations"""
        with open(self.data_path, 'r', encoding='utf-8') as f:
            annotations = json.load(f)
        
        samples = []
        for item in annotations:
            # Extract relevant fields from Label Studio export
            audio_url = item['data'].get('audio_url', '')
            error_types = item['annotations'][0]['result'].get('value', {}).get('choices', [])
            
            # Binary label: 1 if this error type present, 0 otherwise
            label = 1 if self.error_type in error_types else 0
            
            # Get time boundaries if available
            start_time = item.get('start_time', 0.0)
            end_time = item.get('end_time', self.duration)
            
            samples.append({
                'audio_path': audio_url,
                'label': label,
                'start_time': start_time,
                'end_time': end_time,
                'metadata': item
            })
        
        return samples
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        sample = self.samples[idx]
        
        # Load audio
        waveform, sr = torchaudio.load(sample['audio_path'])
        
        # Resample if necessary
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)
        
        # Convert to mono
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        # Crop or pad to fixed length
        if waveform.shape[1] > self.target_length:
            waveform = waveform[:, :self.target_length]
        elif waveform.shape[1] < self.target_length:
            padding = self.target_length - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, padding))
        
        # Apply transforms (augmentation)
        if self.transform:
            waveform = self.transform(waveform)
        
        # Convert to mel spectrogram
        mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.sample_rate,
            n_fft=1024,
            hop_length=160,
            n_mels=64
        )
        mel_spec = mel_transform(waveform)
        mel_spec = torch.log(mel_spec + 1e-9)  # Log scale
        
        label = sample['label']
        
        return mel_spec, label


class TajweedClassifier(nn.Module):
    """
    Tajweed Error Classifier
    
    Architecture: ResNet-18 (pretrained on ImageNet) + BiLSTM + Classifier head
    """
    
    def __init__(self, num_classes: int = 2):
        super().__init__()
        
        # Use pretrained ResNet-18 as feature extractor
        from torchvision.models import resnet18, ResNet18_Weights
        resnet = resnet18(weights=ResNet18_Weights.DEFAULT)
        
        # Remove final classification layer
        self.feature_extractor = nn.Sequential(*list(resnet.children())[:-2])
        
        # Temporal modeling with BiLSTM
        self.lstm = nn.LSTM(
            input_size=512,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.3
        )
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        # x shape: (batch, 1, n_mels, time)
        
        # Repeat grayscale to 3 channels for ResNet
        x = x.repeat(1, 3, 1, 1)
        
        # Feature extraction
        features = self.feature_extractor(x)  # (batch, 512, h, w)
        
        # Flatten spatial dimensions
        batch, channels, h, w = features.shape
        features = features.permute(0, 3, 1, 2).reshape(batch, w, -1)
        
        # LSTM
        lstm_out, _ = self.lstm(features)  # (batch, time, 256)
        
        # Global average pooling over time
        pooled = torch.mean(lstm_out, dim=1)  # (batch, 256)
        
        # Classification
        logits = self.classifier(pooled)
        
        return logits


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device
) -> float:
    """Train for one epoch"""
    model.train()
    total_loss = 0.0
    
    for batch_idx, (inputs, labels) in enumerate(dataloader):
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
        if batch_idx % 10 == 0:
            logger.info(f"Batch {batch_idx}/{len(dataloader)}, Loss: {loss.item():.4f}")
    
    return total_loss / len(dataloader)


def validate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, float]:
    """Validate the model"""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    avg_loss = total_loss / len(dataloader)
    accuracy = 100 * correct / total
    
    return avg_loss, accuracy


def main(args):
    """Main training loop"""
    # Set device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Initialize wandb (optional)
    if args.use_wandb:
        wandb.init(project="qari-tajweed", config=vars(args))
    
    # Load dataset
    dataset = TajweedDataset(
        data_path=args.data_path,
        error_type=args.error_type,
        sample_rate=16000,
        duration=1.0
    )
    
    # Split into train/val
    train_size = int(0.85 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=4
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=4
    )
    
    # Initialize model
    model = TajweedClassifier(num_classes=2).to(device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5)
    
    # Training loop
    best_val_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(args.epochs):
        logger.info(f"\n=== Epoch {epoch+1}/{args.epochs} ===")
        
        # Train
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        logger.info(f"Train Loss: {train_loss:.4f}")
        
        # Validate
        val_loss, val_accuracy = validate(model, val_loader, criterion, device)
        logger.info(f"Val Loss: {val_loss:.4f}, Val Accuracy: {val_accuracy:.2f}%")
        
        # Learning rate scheduling
        scheduler.step(val_loss)
        
        # Log to wandb
        if args.use_wandb:
            wandb.log({
                'epoch': epoch,
                'train_loss': train_loss,
                'val_loss': val_loss,
                'val_accuracy': val_accuracy
            })
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            
            checkpoint_path = Path(args.output_dir) / f"{args.error_type}_best.pth"
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'val_accuracy': val_accuracy
            }, checkpoint_path)
            logger.info(f"Saved best model to {checkpoint_path}")
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= args.patience:
            logger.info(f"Early stopping triggered after {epoch+1} epochs")
            break
    
    logger.info("Training complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train tajweed error classifier")
    parser.add_argument('--data_path', type=str, required=True, 
                        help='Path to Label Studio JSON export')
    parser.add_argument('--error_type', type=str, required=True,
                        choices=['madd_short', 'madd_long', 'ghunnah_missing', 
                                'qalqalah_missing', 'substituted_letter'],
                        help='Type of error to train for')
    parser.add_argument('--output_dir', type=str, default='./models/checkpoints',
                        help='Directory to save model checkpoints')
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--learning_rate', type=float, default=1e-4)
    parser.add_argument('--patience', type=int, default=5,
                        help='Early stopping patience')
    parser.add_argument('--use_wandb', action='store_true',
                        help='Use Weights & Biases for logging')
    
    args = parser.parse_args()
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    main(args)
