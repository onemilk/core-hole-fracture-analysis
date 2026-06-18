"""Preprocess MFAPNet dataset for U-Net training."""
import os
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

RAW_DIR = "raw/MFAPNet/CHA355"

class CoreHoleDataset(Dataset):
    def __init__(self, split='train', train_ratio=0.85):
        self.image_dir = os.path.join(RAW_DIR, "JPEGImages")
        self.mask_dir = os.path.join(RAW_DIR, "SegmentationClass")
        self.files = sorted([f.replace('.jpg', '') for f in os.listdir(self.image_dir)])
        split_idx = int(len(self.files) * train_ratio)
        if split == 'train':
            self.files = self.files[:split_idx]
        else:
            self.files = self.files[split_idx:]

        self.img_transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])
        self.mask_transform = transforms.Compose([
            transforms.Resize((256, 256), interpolation=transforms.InterpolationMode.NEAREST),
            transforms.ToTensor()
        ])

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        name = self.files[idx]
        img = Image.open(os.path.join(self.image_dir, f"{name}.jpg")).convert('RGB')
        mask = Image.open(os.path.join(self.mask_dir, f"{name}.png"))
        mask = np.array(mask)
        mask = (mask > 0).astype(np.float32)
        mask = Image.fromarray((mask * 255).astype(np.uint8))
        return self.img_transform(img), self.mask_transform(mask)

def get_dataloaders(batch_size=8):
    train_ds = CoreHoleDataset(split='train')
    val_ds = CoreHoleDataset(split='val')
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    return train_loader, val_loader

if __name__ == "__main__":
    train_loader, val_loader = get_dataloaders()
    imgs, masks = next(iter(train_loader))
    print(f"Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")
    print(f"Image shape: {imgs.shape}, Mask shape: {masks.shape}")
    print("Preprocessing OK")
