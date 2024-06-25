# ViTAA &middot; [![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/carlos.flores/vitaa/blob/main/LICENSE)

## Versions

- docker: Docker version 24.0.7, build afdd53b
- python: 3.10.13

## Observer's segmentation format

Make sure your label filenames follow this format: `O[N].RevN.txt`. Here, **N** is a number like *2*, and **RevN** is a revision like *Rev01*. For example, `O2.Rev01.txt`.

## Configuration

Customize **config.json**:

- **test_audioFragmentDuration**: Set the maximum duration of audio segments as a whole number. For example, if an observer label's maximum duration is 92.56 seconds, round it up to 93.
- **audacityDataLabelingFilePath**: Specify the directory path where the observer's labels are stored. For example: "/app/labels/".
- **rev**: Choose the file's revision to process. If a label folder contains multiple files from Observers 1 and 2 with various revisions like Rev01, Rev02, etc., select the desired revision. For example: "Rev01".
- **labels**: Provide a list of labels as strings. For example: ["R", "BV", "M", "N", "T"].
- **labelColors**: Assign colors to the labels for visualization. Provide a list of color names corresponding to each label. For example: ["black", "green", "purple", "yellow", "blue"].
- **offset**: Specify a time offset as a decimal number if necessary. This represents the maximum tolerance between observer labeling to reach an agreement. For example: 0.150.
- **outputPath**: Define the directory path where the HTML graph will be saved. For example: "/app/out/".
- **framing**: INTERNAL. Set the framing duration in milliseconds. For example: 10
- **padding**: Define the label to use when there's no explicit labeling in a section. For instance, if there's no labeling between 30.5 and 30.9 seconds, this label will fill the gap. For example: "R".
- **removeNumberFromLabels**: Decide whether to remove numbers from labels if they exist. For example: true.

Note: Adjust these settings according to your requirements to customize the processing of your data.

## Usage

To build the image:
```docker
docker build -t vitaa .
```
To run the sidecar container:
```
docker run --name vitaa -v ./config.json:/app/config.json -v ./out:/app/out --rm vitaa
```

### License

ViTAA is [MIT licensed](./LICENSE).
