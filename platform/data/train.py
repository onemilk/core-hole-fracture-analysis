"""Train U-Net on MFAPNet dataset."""
import os
import torch
import torch.nn as nn
from tqdm import tqdm
from model import UNet
from preprocess import get_dataloaders

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

device = torch.device("cpu")
print(f"Using device: {device}")

model = UNet(in_ch=3, out_ch=1).to(device)
criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)

train_loader, val_loader = get_dataloaders(batch_size=4)
epochs = 100
best_loss = float("inf")

for epoch in range(epochs):
    model.train()
    train_loss = 0
    for imgs, masks in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
        imgs, masks = imgs.to(device), masks.to(device)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, masks)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()

    train_loss /= len(train_loader)

    model.eval()
    val_loss = 0
    with torch.no_grad():
        for imgs, masks in val_loader:
            imgs, masks = imgs.to(device), masks.to(device)
            val_loss += criterion(model(imgs), masks).item()
    val_loss /= len(val_loader)

    scheduler.step(val_loss)
    print(f"Epoch {epoch+1}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

    if val_loss < best_loss:
        best_loss = val_loss
        torch.save(model.state_dict(), os.path.join(MODEL_DIR, "unet_best.pt"))
        print(f"  Saved best model (val_loss={val_loss:.4f})")

# Export
model.load_state_dict(torch.load(os.path.join(MODEL_DIR, "unet_best.pt")))
model.eval()
example = torch.randn(1, 3, 256, 256)
traced = torch.jit.trace(model, example)
traced.save(os.path.join(MODEL_DIR, "unet_traced.pt"))
print(f"Model exported to {MODEL_DIR}/unet_traced.pt")
