import torch
from torchvision import datasets, transforms

from src.mnist.model import Net


def pred_single_image(model: Net, device: str, image_path: str) -> int:
    transform = transforms.Compose(
        [
            transforms.Grayscale(num_output_channels=1),
            transforms.ToTensor(),
            transforms.Normalize(
                (0.1307,),
                (0.3081,),
            ),
        ],
    )

    image = datasets.folder.default_loader(image_path)
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(image)
        pred = output.argmax(dim=1, keepdim=True)
        return pred.item()
