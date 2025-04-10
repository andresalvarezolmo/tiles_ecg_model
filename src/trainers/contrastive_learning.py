import torch, torch.nn as nn
from torch import Tensor

from simclr.modules import NT_Xent, LARS
from pytorch_lightning import LightningModule


class ContrastiveLearning(LightningModule):
    def __init__(self, args, encoder: nn.Module):
        super().__init__()
        self.save_hyperparameters(args)

        # backbone encoder
        self.encoder = encoder
        # dimensionality of representation
        self.n_features = self.encoder.output_size
        # projection head
        self.projector = nn.Sequential(
            nn.Linear(self.n_features, self.n_features, bias=False),
            nn.ReLU(),
            nn.Linear(self.n_features, self.hparams.projection_dim, bias=False),
        )
        self.model = nn.Sequential(self.encoder, self.projector)

        # criterion function
        self.criterion = self.configure_criterion()

    def forward(self, x_i: Tensor, x_j: Tensor) -> Tensor:
        z_i = self.model(x_i.unsqueeze(1))
        z_j = self.model(x_j.unsqueeze(1))
        return self.criterion(z_i, z_j)

    def training_step(self, batch, _) -> Tensor:
        x = batch
        loss = self.forward(x[:, 0, :], x[:, 1, :])
        self.log("Train/loss", loss, sync_dist=True)
        return loss

    def validation_step(self, batch, _) -> Tensor:
        x = batch
        loss = self.forward(x[:, 0, :], x[:, 1, :])
        self.log("Valid/loss", loss, sync_dist=True)
        return loss

    def configure_criterion(self) -> nn.Module:
        # PL aggregates differently in DP mode
        if self.hparams.accelerator == "dp" and self.hparams.gpus:
            batch_size = int(self.hparams.batch_size / self.hparams.gpus)
        else:
            batch_size = self.hparams.batch_size

        return NT_Xent(batch_size, self.hparams.temperature, world_size=1)

    def configure_optimizers(self) -> dict:
        if self.hparams.optimizer == "Adam":
            optimizer = torch.optim.AdamW(
                self.model.parameters(), lr=self.hparams.learning_rate)
        else:
            raise NotImplementedError
        return {"optimizer": optimizer}
