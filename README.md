# hel

## Versions

- docker: Docker version 24.0.7, build afdd53b
- python: 3.10.13

## Labels format

the filename of label must follow: `ON.REVN.txt`
where **ON** must be **O** and **N** a number like *2*, where **REVN** must be some revision like *Rev01* and must match to the rev configuration e.g. `O2.Rev01.txt`

## Configuration

Modify **config.json**:
- **test_audioFragmentDuration**: integer, the maximum of the audio segmentation. e.g. if the max in some observer label is 92,56 then need to put 93.
- **audacityDataLabelingFilePath**: string, The path where the observer's label. e.g. "/app/labels/"
- **rev**: string, the file's revision to process. A label's folder can contains multiples files of Observer 1 and 2 with multiples revision like Rev01, Rev02, etc, this is for select one of that revision. e.g. "Rev01"
- **labels**: string array. e.g. ["R", "BV", "M", "N", "T"]
- **labelColors**: string array. e.g. ["black", "green", "purple", "yellow", "blue"]
- **offset**: float. e.g. 0.150
- **outputPath**: string. e.g. "/app/out/"
- **framing**: number, milliseconds. e.g. 10
- **padding**: string, the label to fill when labeling contains 'no-label' section. If from 30,5 to 30,9 has no labeling then it will fill using this. e.g. "R"
- **removeNumberFromLabels**: bool. if some label contains a number then it will remove the number. e.g. true

## Use

To build the image:
```docker
docker build -t hel .
```
To run the sidecar container:
```
docker run --name hel -v ./config.json:/app/config.json -v ./out:/app/out --rm hel
```
