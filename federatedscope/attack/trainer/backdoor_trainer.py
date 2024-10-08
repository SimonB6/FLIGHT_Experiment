import logging
from typing import Type
import torch
import numpy as np
import copy

from federatedscope.core.trainers import GeneralTorchTrainer
from torch.nn.utils import parameters_to_vector, vector_to_parameters

logger = logging.getLogger(__name__)


def wrap_backdoorTrainer(
        base_trainer: Type[GeneralTorchTrainer]) -> Type[GeneralTorchTrainer]:
    '''
    Warp the trainer for backdoor attack:

    poisoning data:
        edge-case triggers
        semantic triggers
        pixel-wise triggers: badnet, blended(HK), sig, wanet, clean-label (narcissus)

    poisoning model:
        black-box attacks
        PGD training
        local regularization

    Args:
        base_trainer: Type: core.trainers.GeneralTorchTrainer

    :returns:
        The wrapped trainer; Type: core.trainers.GeneralTorchTrainer

    '''

    # ---------------- attribute-level plug-in -----------------------
    # for pFL, we need to know the type of used methods.
    base_trainer.ctx.federate_method = base_trainer.cfg.federate.method
    base_trainer.ctx.target_label_ind = base_trainer.cfg.attack.target_label_ind
    base_trainer.ctx.trigger_type = base_trainer.cfg.attack.trigger_type
    base_trainer.ctx.label_type = base_trainer.cfg.attack.label_type
    '''
    You can add trigger type: edge-case triggers and semantic triggers.
    '''

    # ---- action-level plug-in -------

    if base_trainer.cfg.attack.self_opt:

        base_trainer.ctx.self_lr = base_trainer.cfg.attack.self_lr
        base_trainer.ctx.self_epoch = base_trainer.cfg.attack.self_epoch

        base_trainer.register_hook_in_train(
            new_hook=hook_on_fit_start_init_local_opt,
            trigger='on_fit_start',
            insert_pos=-1)

        base_trainer.register_hook_in_train(new_hook=hook_on_fit_end_reset_opt,
                                            trigger='on_fit_end',
                                            insert_pos=0)

    if base_trainer.cfg.attack.scale_poisoning or base_trainer.cfg.attack.pgd_poisoning:

        base_trainer.register_hook_in_train(
            new_hook=hook_on_fit_start_init_local_model,
            trigger='on_fit_start',
            insert_pos=-1)

    if base_trainer.cfg.attack.scale_poisoning:

        base_trainer.ctx.scale_para = base_trainer.cfg.attack.scale_para

        base_trainer.register_hook_in_train(
            new_hook=hook_on_fit_end_scale_poisoning,
            trigger="on_fit_end",
            insert_pos=-1)

    if base_trainer.cfg.attack.pgd_poisoning:

        base_trainer.ctx.self_epoch = base_trainer.cfg.attack.self_epoch
        base_trainer.ctx.pgd_lr = base_trainer.cfg.attack.pgd_lr
        base_trainer.ctx.pgd_eps = base_trainer.cfg.attack.pgd_eps
        base_trainer.ctx.batch_index = 0

        base_trainer.register_hook_in_train(
            new_hook=hook_on_fit_start_init_local_pgd,
            trigger='on_fit_start',
            insert_pos=-1)

        base_trainer.register_hook_in_train(
            new_hook=hook_on_batch_end_project_grad,
            trigger='on_batch_end',
            insert_pos=-1)

        base_trainer.register_hook_in_train(
            new_hook=hook_on_epoch_end_project_grad,
            trigger='on_epoch_end',
            insert_pos=-1)

        base_trainer.register_hook_in_train(new_hook=hook_on_fit_end_reset_opt,
                                            trigger='on_fit_end',
                                            insert_pos=0)

    return base_trainer


def hook_on_fit_start_init_local_opt(ctx):

    # need to check for ditto method
    # ctx.original_optimizer = ctx.optimizer

    if ctx.federate_method.lower() == "ditto":
        ctx.original_epoch = ctx["num_train_epoch"]
        ctx["num_train_epoch"] = ctx.self_epoch + ctx.num_train_epoch_for_local_model

    elif ctx.federate_method.lower() == "fedrep":
        ctx.original_epoch = ctx["num_train_epoch"]
        ctx["num_train_epoch"] = ctx.self_epoch + ctx.epoch_linear
    else:
        ctx.original_epoch = ctx["num_train_epoch"]
        ctx["num_train_epoch"] = ctx.self_epoch


def hook_on_fit_end_reset_opt(ctx):

    ctx["num_train_epoch"] = ctx.original_epoch


def hook_on_fit_start_init_local_model(ctx):

    ctx.original_model = copy.deepcopy(ctx.model)  # the original global model


def hook_on_fit_end_scale_poisoning(ctx):

    # conduct the scale poisoning
    scale_para = ctx.scale_para

    v = torch.nn.utils.parameters_to_vector(ctx.original_model.parameters())
    logger.info("the Norm of the original global model: {}".format(
        torch.norm(v)))

    v = torch.nn.utils.parameters_to_vector(ctx.model.parameters())
    logger.info("Attacker before scaling : Norm = {}".format(torch.norm(v)))

    ctx.original_model = list(ctx.original_model.parameters())

    for idx, param in enumerate(ctx.model.parameters()):
        param.data = (param.data - ctx.original_model[idx]
                      ) * scale_para + ctx.original_model[idx]

    v = torch.nn.utils.parameters_to_vector(ctx.model.parameters())
    logger.info("Attacker after scaling : Norm = {}".format(torch.norm(v)))

    logger.info('finishing model scaling poisoning attack'.format())


def hook_on_fit_start_init_local_pgd(ctx):

    ctx.original_optimizer = ctx.optimizer
    ctx.original_epoch = ctx["num_train_epoch"]
    ctx["num_train_epoch"] = ctx.self_epoch
    ctx.optimizer = torch.optim.SGD(ctx.model.parameters(), \
                                    lr=ctx.pgd_lr, momentum=0.9, weight_decay=1e-4)


def hook_on_batch_end_project_grad(ctx):

    eps = ctx.pgd_eps
    project_frequency = 10
    ctx.batch_index += 1
    w = list(ctx.model.parameters())
    w_vec = parameters_to_vector(w)
    model_original_vec = parameters_to_vector(
        list(ctx.original_model.parameters()))
    # make sure you project on last iteration otherwise, high LR pushes you really far
    if (ctx.batch_index % project_frequency
            == 0) and (torch.norm(w_vec - model_original_vec) > eps):
        # project back into norm ball
        w_proj_vec = eps * (w_vec - model_original_vec) / torch.norm(
            w_vec - model_original_vec) + model_original_vec
        # plug w_proj back into model
        vector_to_parameters(w_proj_vec, w)


def hook_on_epoch_end_project_grad(ctx):

    ctx.batch_index = 0
    eps = ctx.pgd_eps
    w = list(ctx.model.parameters())
    w_vec = parameters_to_vector(w)
    model_original_vec = parameters_to_vector(
        list(ctx.original_model.parameters()))
    # make sure you project on last iteration otherwise, high LR pushes you really far
    if (torch.norm(w_vec - model_original_vec) > eps):
        # project back into norm ball
        w_proj_vec = eps * (w_vec - model_original_vec) / torch.norm(
            w_vec - model_original_vec) + model_original_vec
        # plug w_proj back into model
        vector_to_parameters(w_proj_vec, w)


def hook_on_fit_end_reset_pgd(ctx):

    pass
