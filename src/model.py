from torch import nn


class BlockEg(nn.Module):
    def __init__(self, input_size: int = 180):  # important to define default values
        super().__init__()
        self.layer1 = nn.Linear(input_size, 32)

    def forward(self, x):
        return self.layer1(x)


class DNN(nn.Module):
    def __init__(
        self,
        input_size: int = 180,
        output_size: int = 10,
        layer_widths: tuple[int, ...] = (5, 10, 5),
        block: BlockEg = BlockEg(),  # so that up the stack the default values are set
        fc: nn.Linear = nn.Linear(32, 10),  # initialize with whatever - we'll override
    ):
        super().__init__()
        self.input_size = input_size
        self.output_size = output_size
        self.layer_widths = layer_widths
        self.block = block  # not overriden as default set by user
        self.fc = nn.Linear(32, output_size)  # override as defaults aren't set by Torch

    def forward(self, x):
        x = self.block(x)
        return self.fc(x)


    #     # prepare trainable model for train synchronizations - wrapper for DDP
    #     self.models.dnn = prepare_model(self.models.dnn)

    #     # NOTE - prepare non-trained model for inference
    #     # self.models.resnet = self.models.resnet.to(get_device())

    #     train_loader, _, _ = self.generate_loaders(dataset_shards=dataset_shards)

    #     for epoch in range(self.cfg.start_epoch, self.cfg.num_epochs):
    #         print(
    #             f"Epoch START: {epoch}, world rank: {train.get_context().get_world_rank()}"
    #         )

    #         self.train_steps(dataloader=train_loader, epoch=epoch)

    #         dummy_val_loss = 69
    #         if self.tools.early_stoppage(dummy_val_loss):
    #             print(f"Early stopping at epoch {epoch}")
    #             break

    #         self.save_checkpoint(
    #             epoch=epoch,
    #             metrics={},
    #         )

    # def train_steps(self, dataloader: DataLoader, epoch: int):
    #     self.reset_all_metrics_and_losses()
    #     for batch_idx, batch in enumerate(dataloader):
    #         x = batch["inputs"]
    #         y = batch["label"]

    #         output = self.models.dnn(x)

    #         # local loss compute and gradient calculation
    #         loss = self.losses.loss1(output, y)
    #         loss.backward()

    #         # updating losses and metrics as desired
    #         # NOTE: you will get warnings if you save metrics & losses without updating them
    #         self.losses.loss1.update(output, y)
    #         self.metrics.mae.update(output, y)

    #         self.save_metrics_and_losses(
    #             batch_idx=batch_idx,
    #             epoch=epoch,
    #         )

    #         self.optimizers.adam.step()
    #         self.optimizers.adam.zero_grad()

    #         self.tools.lr_scheduler.step(self.optimizers.adam)
