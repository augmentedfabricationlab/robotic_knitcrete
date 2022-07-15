# Knit patterns
Code for the generation (from a text file or a spreadsheet) and post-processing of knit patterns.

## Requirements:
* Virtual environment with the dependencies listed in `requirements.txt` installed.

### Installation instructions for conda:
* Activate the conda virtual environment by running: `conda activate robknit`
* Path to the correct folder: `cd C:\Users\YOUR_USERNAME\workspace\robotic_knitcrete\src\knitting`
* To install python packages from a `requirements.txt` file while in the environment: `pip install -r requirements.txt`

## Usage:
    python cli.py generate-from-source ...
Pattern generator command

Options:
* `--color-settings PATH`   
Path to JSON file containing knit operations mapped to RGB values
* `--image-width INTEGER`   
Image width (in pixels). If undefined or None, the image width will be the same as the width of the input pattern.
* `--image-height INTEGER`  
Image height (in pixels). If undefined or None, the image height will be the same as the height of the input pattern.
* `--output-dir PATH`       
Output directory to store the images in

------------------------------------------

    python cli.py post-process ...
Post processes existing pattern

Options:
* `--help`  Show options.
