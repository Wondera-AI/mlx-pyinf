from typing import Any

import torch
from pydantic import BaseModel

from src.mnist.inference import pred_single_image
from src.mnist.model import load_model


class Request(BaseModel):
    path_image: str
    path_model: str = "src/mnist/pretrained/test_mnist.pt"


class RunArgs(BaseModel):
    use_mps: bool = False
    use_gpu: bool = False
    optional_smoothing: int = 10


class Service:
    def __call__(self, request: Request, args: RunArgs) -> Any:
        print("Inside Service")
        print("Image path requested", request.path_image)

        device = torch.device(
            "mps"
            if torch.backends.mps.is_available()
            else "cuda"
            if torch.cuda.is_available()
            else "cpu",
        )
        if device == "mps" and args.use_mps:
            device = "cpu"
        if device == "cuda" and args.use_gpu:
            device = "cuda"

        model = load_model(request.path_model, device)

        pred = pred_single_image(model, str(device), request.path_image)

        print("Prediction", pred)

        return pred
