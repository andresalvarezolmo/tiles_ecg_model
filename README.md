

<div align="center">

# WildECG: Ubiquitous ECG Pre-Training
This repo contains code implementation as well as trained models for ECG data analysis.
  
</div>

## Installation

We recommend using a conda environment with ``Python >= 3.9`` :

```bash
conda create -n tiles_ecg python=3.9
conda activate tiles_ecg
```

Clone the repository and install the dependencies:

```bash
git clone https://github.com/klean2050/tiles_ecg_model
pip install -e tiles_ecg_model
```

You will also need the ``ecg-augmentations`` library:

```bash
git clone https://github.com/klean2050/ecg-augmentations
pip install -e ecg-augmentations
```

## Project Structure

```bash
tiles_ecg_model/
├── setup.py             # package installation script
├── examples.ipynb       # temporary/demostrative code
├── config/              # configuration files for each train session
├── ckpt/                # pre-trained models available for fine-tuning
└── src/                 # main project directory
    ├── loaders/             # pytorch dataset classes
    ├── models/              # backbone neural network models
    ├── scripts/             # preprocess, training and evaluation
    ├── trainers/            # lightning classes for each train session
    └── utils/               # miscellaneous scripts and methods
```

## TILES Dataset

Tracking Individual Performance with Sensors (TILES) is a project holding multimodal data sets for the analysis of stress, task performance, behavior, and other factors pertaining to professionals engaged in a high-stress workplace environments. Biological, environmental, and contextual data was collected from hospital nurses, staff, and medical residents both in the workplace and at home over time. Labels of human experience were collected using a variety of psychologically validated questionnaires sampled on a daily basis at different times during the day. In this work, we utilize the TILES ECG data from the publicly available dataset, that we download from [here](https://tiles-data.isi.edu/).

## Pre-Training Framework

Each TILES participant has their ECG recorded for 15 seconds every 5 minutes during their work hours, for a total of 10 weeks. Here we extract all available 15-sec ECG segments and eliminate those with quality (i.e., rate of R peak identification) less than 90%. We end up with ~275,000 samples which we downsample to 100Hz, filter with a 0.5-40Hz Butterworth and normalize per subject. To preprocess TILES data, run the following command:

```bash
python src/scripts/preprocess.py
```

The same preprocessing pipeline is used for every dataset during fine-tuning, implemented in ``loaders``.

We pre-train the model in a self-supervised manner, through transform identification. To transform the ECG samples we use the [PyTorch ECG Augmentations](https://github.com/klean2050/ecg-augmentations) package. First, the input ECG is randomly cropped to 10 seconds and a series of masks and signal transformations are randomly applied based on a set probability. The network is then trained to identify which transformations were applied. We use a lightweight [S4](https://github.com/HazyResearch/state-spaces) model as backbone. Command:

```bash
python src/scripts/ssl_pretrain.py
```

## Fine-Tuning Framework

Pre-trained models, described at ``ckpt``, are shared to the research community, and should not be used for clinical purposes. One can transfer the trained ECG encoder to model downstream tasks, ranging from clinical condition estimation, affect perception, stress and interaction analysis. To view training logs in TensorBoard run:

```bash
tensorboard --logdir ./runs
```

## Acknowledgements

In this study we made use of the following repositories:

* [VCMR](https://github.com/klean2050/VCMR) (repo template)
* [ecg-augmentations](https://github.com/klean2050/ecg-augmentations)

## Citation

If you use WildECG in your own study, please consider citing accordingly:

```
@misc{avramidis2023scaling,
    title={Scaling Representation Learning from Ubiquitous ECG with State-Space Models}, 
    author={Kleanthis Avramidis and Dominika Kunc and Bartosz Perz and Kranti Adsul and Tiantian Feng and Przemysław Kazienko and Stanisław Saganowski and Shrikanth Narayanan},
    year={2023},
    eprint={2309.15292},
    archivePrefix={arXiv},
}

@article{mundnich2020tiles,
    title={TILES-2018, a longitudinal physiologic and behavioral data set of hospital workers},
    author={Mundnich, Karel and Booth, Brandon M and l’Hommedieu, Michelle and Feng, Tiantian and Girault, Benjamin and L’hommedieu, Justin and Wildman, Mackenzie and Skaaden, Sophia and Nadarajan, Amrutha and Villatte, Jennifer L and others},
    journal={Scientific Data},
    volume={7},
    number={1},
    pages={354},
    year={2020},
    publisher={Nature Publishing Group UK London}
}
```
The accompanying [paper](https://arxiv.org/abs/2309.15292) has been submitted to IEEE Journal of Biomedical and Health Informatics (2023).
The project is supported by Toyota Motor North America (TMNA) and MIRISE Technologies.
