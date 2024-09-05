from typing import Any

import torch
from pydantic import BaseModel

from src.mnist.inference import pred_single_image
from src.mnist.model import load_model


class Request(BaseModel):
    path_image: str
    path_model: str = "src/mnist/pretrained/test_mnist.pt"


class DeploymentArgs(BaseModel):
    use_mps: bool = False
    use_gpu: bool = False
    optional_smoothing: int = 10


class Service:
    def __call__(self, request: Request, args: DeploymentArgs) -> Any:
        print("Inside Service")
        print("Image path requested", request.path_image)

        # @rust-generalization: hardware selection automatic in Burn
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

        # @rust-generalization: loading should standardize
        model = load_model(request.path_model, device)

        # @rust-generalization: keeping inference logic in one function for clean code
        # NOTE-devs: this will assist in Rust ONNX acceleration deployments
        pred = pred_single_image(model, str(device), request.path_image)

        print("Prediction", pred)

        return pred
