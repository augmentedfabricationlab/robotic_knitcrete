# Knit patterns
Code for the generation (from a text file or a spreadsheet) and post-processing of knit patterns.

## Requirements:
* Virtual environment with the dependencies listed in `requirements.txt` installed.

### Installation instructions for conda:
* Create a conda virtual environment by running: `conda create --name <env_name> python=3.7`
* Activate new conda environment: `conda activate <env_name>`
* To install python packages from a `requirements.txt` file while in the environment: `pip install -r requirements.txt`

## Usage:
* Run `python cli.py generate-from-source ...` for the pattern generator command.
* Run `python cli.py post-process ...` for the pattern post-processing commands.
